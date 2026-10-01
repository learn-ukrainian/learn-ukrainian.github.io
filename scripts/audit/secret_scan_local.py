#!/usr/bin/env python3
"""Offline local TruffleHog scan whose console output carries no finding-derived text.

Runbook: docs/runbooks/secret-scanning.md (#9416).

Threat model: the operator's agents run this wrapper as the operator's own user.
Hostile data comes from the scanned content, the fields of each finding, the
configured remote and the command-line options. Other processes of the same user
racing to move directories, hardlink files or bind-mount are out of scope: they
could write the files directly.

Safety properties, each covered by tests/audit/test_secret_scan_local.py:

* verification is never enabled: ``--no-verification`` is always passed and any
  verification-style option on the wrapper's command line is refused;
* the console carries no finding-derived text: totals, a count per detector name
  from the closed set ``KNOWN_DETECTORS`` (any other name is counted as
  ``other``), exit codes and fixed messages. No path, commit, line, key value or
  placeholder is printed. ``show-keys`` prints a report's top-level keys from the
  closed set ``REPORT_KEYS`` and the same per-detector counts, nothing else;
* the full report (raw secret values) and TruffleHog's log are created
  exclusively, 0600, in a new 0700 ``mkdtemp`` directory under the system temp
  root; only the generated file name is printed. The run is refused up front
  when the resolved temp root lies inside the repository or its primary checkout;
* every diagnostic is a fixed message that never repeats an option value, a
  path, a remote URL or tool output;
* ``history`` mirror-clones only a plain ``https://`` remote (validated, passed
  after ``--``, transport restricted to https) into a second ``mkdtemp``
  directory by its absolute path and removes it afterwards; a failed removal is
  an error.
"""

from __future__ import annotations

import argparse
import errno
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.parse
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import NoReturn, TextIO

PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2

TRUFFLEHOG = "trufflehog"
IGNORE_FILE = ".trufflehogignore"
DEFAULT_TIMEOUT_SECONDS = 3600
GIT_TIMEOUT_SECONDS = 60
# Bytes of path arguments per ``trufflehog filesystem`` call; well under ARG_MAX.
TREE_BATCH_BYTES = 100_000

# Fixed for every scan. Offline TruffleHog marks every candidate "unverified", so
# CI's ``--results=verified,unknown`` would hide everything; ``unverified`` is the
# offline superset of what CI reports. ``--no-update`` keeps the run offline.
SAFE_FLAGS: tuple[str, ...] = (
    "--json",
    "--no-verification",
    "--no-update",
    "--results=unverified",
    "--exclude-detectors=Lob",
    "--fail-on-scan-errors",
)
FORBIDDEN_FLAG_MARKERS: tuple[str, ...] = ("verif", "--results")

# Never handed to the filesystem scan, whatever .gitignore says.
DENIED_DIR_PARTS = frozenset({".git", ".venv", "node_modules", ".worktrees"})
DATABASE_SUFFIXES = (".db", ".sqlite", ".sqlite3", ".duckdb", ".db-wal", ".db-shm", ".db-journal")

# history: the remote must be a plain https URL, and git may use no other transport
# (also after url.<base>.insteadOf rewrites or redirects).
SAFE_REMOTE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
MAX_REMOTE_URL = 2048
CLONE_PROTOCOLS = "https"

FILE_FLAGS = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
OUTPUT_PREFIX = "secret-scan-"
MIRROR_PREFIX = "secret-scan-mirror-"

# Top-level keys of a TruffleHog JSON result (pkg/output/json.go, v3.97.9).
REPORT_KEYS = frozenset(
    {
        "SourceMetadata",
        "SourceID",
        "SourceType",
        "SourceName",
        "DetectorType",
        "DetectorName",
        "DetectorDescription",
        "DecoderName",
        "Verified",
        "VerificationError",
        "VerificationFromCache",
        "Raw",
        "RawV2",
        "Redacted",
        "ExtraData",
        "StructuredData",
        "SecretParts",
    }
)

# The only detector names the console may print: TruffleHog's DetectorType enum
# (proto/detector_type.proto, v3.97.9), whose value names are a finding's
# DetectorName, sorted. Any other name is counted under OTHER_DETECTOR. When upgrading
# TruffleHog, regenerate this list from that file; a test checks every name against
# the installed binary. Kept as one whitespace-separated block: a list literal would be
# formatted one name per line.
KNOWN_DETECTORS = frozenset(
    """
    Abstract AbuseIPDB Abyssale Accuweather AdafruitIO AdobeIO Adzuna Aerisweather Aeroworkflow Aftership Agora Aha
    AirbrakeProjectKey AirbrakeUserKey Airship AirtableApiKey AirtableMetadataApiKey AirtableOAuth
    AirtablePersonalAccessToken AirVisual Aiven AkamaiToken Alchemy Alconost Alegra AletheiaApi AlgoliaAdminKey
    Alibaba AlienVault Allsports Alphavantage Amadeus AmazonMWS Ambee AmplitudeApiKey AMQP Anthropic Anypoint
    AnypointOAuth2 Apacta Api2Cart Api2Convert ApiDeck Apiflash ApiFonica Apify Apilayer APIMatic ApiMetrics
    ApiScience APITemplate Apollo Appcues Appfollow Appointedd AppOptics AppSynergy Apptivo ArtifactoryAccessToken
    ArtifactoryReferenceToken Artsy AsanaOauth AsanaPersonalAccessToken AssemblyAI Atera Atlassian Audd
    Auth0ManagementApiToken Auth0oauth Authorize Autodesk Autoklose AutoPilot Avalara AvazaPersonalAccessToken
    AviationStack AWS AWSAppSync AWSSessionKey Axonaut Aylien Ayrshare Azure AzureActiveDirectoryApplicationSecret
    AzureApiManagementRepositoryKey AzureAPIManagementSubscriptionKey AzureAppConfigConnectionString AzureBatch
    AzureCacheForRedisAccessKey AzureContainerRegistry AzureCosmosDBKeyIdentifiable AzureDevopsPersonalAccessToken
    AzureDirectManagementKey AzureFunctionKey AzureManagementCertificate AzureMLWebServiceClassicIdentifiableKey
    AzureOpenAI AzureRefreshToken AzureSasToken AzureSearchAdminKey AzureSearchQueryKey AzureSQL AzureStorage
    Bannerbear Baremetrics BaseApiIO BasisTheory Beamer Beebole Besnappy Besttime BetterStack Billomat
    BingSubscriptionKey Bitbar BitbucketAppPassword BitbucketDataCenter BitcoinAverage Bitfinex BitGo
    BitLyAccessToken Bitmex Blablabus Blazemeter BlitApp BlockNative Blogger BombBomb BoostNote Bored Borgbase Box
    BoxOauth BraintreePayments BrainTrustApiKey Brandfetch Brightlocal BrowserStack Browshot BscScan Bubble BuddyNS
    Budibase Bugherd Bugsnag Buildkite BuiltWith Bulbul Bulksms ButterCMS Caflou Calendarific CalendlyApiKey
    CalorieNinja Campayn CannyIo CapsuleCRM CaptainData CarbonInterface Cashboard Caspio Censys CentralStationCRM
    CexIO Chartmogul Chatbot Chatfule ChecIO ChecklyHQ Checkmarket Checkout Checkvist Cicero Circle CircleCI
    Clarifai Clearbit ClickHelp ClickSendsms ClickupPersonalToken Cliengo Clientary Clinchpad Clockify ClockworkSMS
    Close Cloudant CloudConvert CloudElements CloudflareApiToken CloudflareCaKey CloudflareGlobalApiKey CloudImage
    Cloudinary Cloudmersive Cloudplan CloudsightKey Cloudsmith Cloudways Cloverly Cloze ClustDoc Coda Codacy
    Codeclimate Codemagic Codequiry CoinApi Coinbase CoinbaseWaaS CoinGecko Coinlayer Coinlib CoinMarketCap Collect2
    Column Cometchat CommerceJS Commodities CompanyHub ConfluenceDataCenter Confluent ContentfulDelivery
    ContentfulPersonalAccessToken ContentStack ConversionTools Convert ConvertApi Convertkit Convier Copper
    Copyscape Couchbase CountryLayer Courier Coveralls CraftMyPDF Createsend Cricket CrossBrowserTesting Crowdin
    CryptoCompare CurrencyCloud Currencyfreaks Currencylayer CurrencyScoop CurrentsAPI CustomerGuru CustomerIO
    CustomRegex D7Network DailyCO Dandelion Dareboost Databox DatabricksToken DatadogApikey DatadogToken DataFire
    DataGov Debounce DeepAI Deepgram DeepSeek Delighted Demio DenoDeploy Deputy Detectify DetectLanguage Dfuse
    Diffbot Diggernaut DigitalOceanSpaces DigitalOceanToken DigitalOceanV2 DiscordBotToken DiscordWebhook Disqus
    Distribusion Ditto Dnscheck Docker Dockerhub Docparser Documo Docusign Doppler Dotdigital Dovico DronaHQ DroneCI
    Dropbox Duda Duffel DuffelToken Duo Duply Dwolla Dynadot Dynalist Dynatrace Dyspatch EagleEyeNetworks
    EasyInsight EcoStruxureIT Edamam EdenAI Edusign EightxEight ElasticEmail ElasticPath ElevenLabs Emailoctopus
    Enablex EndorLabs Enigma EnvoyApiKey EquinixOauth Eraser Etherscan Ethplorer EtsyApiKey Eventbrite Everhour
    Eversign ExchangeRateAPI ExchangeRatesAPI ExportSDK ExtractorAPI FacebookOAuth FacePlusPlus FakeJSON FastForex
    FastlyPersonalToken Fastspring Feedier Feedly Fetchrss Fibery FigmaPersonalAccessToken FileIO Filestack Finage
    FinancialModelingPrep Findl Finnhub Firebase FirebaseCloudMessaging FixerIO FlagsmithEnvironmentKey
    FlagsmithToken FlatIO Fleetbase Flexport Flickr FlightApi FlightLabs Flightstats Float Flowdash Flowdock FlowFlu
    Flutterwave FlyIO Fmfw FormBucket Formcraft FormIO Formsite Formstack Fountain FourSquare FrameIO Freshbooks
    Freshdesk Front FTP Fulcrum FullContact Fullstory Fusebill FXMarket GCP GCPApplicationDefaultCredentials
    Geckoboard Gemini Generic Gengo Geoapify Geocode Geocodify Geocodio GeoIpifi GetEmail GetEmails GetGeoAPI
    Getgist Getresponse GetSandbox Github GitHubApp GitHubOauth2 GitHubOld Gitlab GitLabOauth2 Gitter Glassnode
    GlitterlyAPI GoCanvas GoCardless GoDaddy GoodDay GoogleApiKey GoogleGeminiAPIKey GoogleOauth2 Goshippo Gosquared
    Grafana GrafanaServiceAccount GraphCMS Graphhopper Groovehq Groq GTMetrix Guardianapi Gumroad Guru Gyazo Happi
    Happyscribe Harness Harvest HashiCorpVaultAuth HashiCorpVaultBatchToken HashiCorpVaultToken Hasura Heatmapapi
    HelloSign HelpCrunch Helpscout HereAPI Heroku Hive Hiveage HolidayAPI Holistic Honey Honeycomb Host Hotwire
    Html2Pdf HubSpot HubSpotApiKey HubSpotOauth HuggingFace Humanity HumioAPIToken Hunter Hybiscus HypeAuditor
    Hypertrack IbmCloudUserKey IconFinder Iexapis Iexcloud Image4 Imagekit ImageToText Imagga Imgix Imgur Impala
    Infobip Infura Insightly Instabot Instamojo Integromat Intercom Interseller Intra42 Intrinio InvoiceOcean
    Ip2location Ipapi IPGeolocation Ipify IPInfo IPinfoDB IPQuality IpStack JDBC JiraDataCenterPAT JiraToken Jotform
    JSONbin Jumpcloud Jumpseller JupiterOne Juro JWT Kairos KakaoTalk Kaleyra KalturaAppToken KalturaSession Kanban
    Kanbantool KarmaCRM KeenIO Keygen Kickbox KiteConnect Klaviyo Klipfolio KnapsackPro Kontent Kraken KubeConfig
    KuCoin Kylas Langfuse LangSmith LanguageLayer LarkSuite LarkSuiteApiKey Lastfm LaunchDarkly LDAP Leadfeeder
    Lemlist LemonSqueezy Lendflow LessAnnoyingCRM Lexigram LinearAPI LineMessaging LineNotify LinkedIn LinkPreview
    Linode LiveAgent Livestorm Loadmill Lob LocationIQ Loggly Loginradius LogzIO LokaliseToken Loyverse LunchMoney
    Luno M3o Macaddress MadKudu MagicBell Magnetic Mailboxlayer Mailchimp Mailerlite Mailgun MailJetBasicAuth
    MailJetSMS Mailmodo Mailsac Mandrill Manifest MapBox Mapquest Marketstack MattermostPersonalToken Mavenlink
    MaxMindLicense MeaningCloud MediaStack Meistertask Meraki Mesibo MessageBird Messari MetaAPI Metabase Metrilo
    MicrosoftTeamsWebhook Midise Mindmeister Miro Mite Mixcloud Mixmax Mixpanel Mockaroo Moderation Mojohelpdesk
    MollieAccessToken MollieAPIKey Monday MongoDB MonkeyLearn Moonclerk Moosend Moralis Mrticktock Mux Myexperiment
    Myfreshworks MyIntervals NasdaqDataLink NetCore Nethunt Netlify Netsuite NeutrinoApi NewRelicBrowserKey
    NewRelicInsightsInsertKey NewRelicInsightsQueryKey NewRelicLicenseKey NewRelicMobileAppToken
    NewRelicPersonalApiKey NewRelicUserKey Newsapi Newscatcher NexmoApiKey Nftport NGC Ngrok NiceHash Nicereply
    Nightfall Nimble Nitro Nordigen Noticeable Notion NozbeTeams NpmToken Nubela NuGetApiKey Numverify Nutritionix
    NVAPI Nylas Nytimes Oanda OcrSpace OctopusDeploy Okta Omnisend Onbuka Onedesk OneLogin OnepageCRM Onesignal
    Onfleet OnWaterIO OOPSpam OpenAI OpenAIAdmin OpenCageData Opendatasoft Opengraphr OpenRouter Openuv OpenVpn
    OpenWeather Opsgenie Optidash Optimizely Overloop Owlbot PackageCloud Paddle Pagarme Page2Images PagerDutyApiKey
    Pandadoc PandaScore Paperform Papyrs ParallelDots Parsehub Parsers Parseur Partnerstack Passbase Pastebin
    Paydirtapp Paymo Paymoapp Paymongo PaypalOauth Paystack PdfLayer PDFmyURL PdfShift PendoIntegrationKey
    PeopleDataLabs Pepipost Percy PgAnalyzeReadKey Photoroom PhraseAccessToken Pinata Pinecone Pipedream Pipedrive
    PivotalTracker Pixabay PlaidKey PlaidToken PlanetScale PlanetScaleDb PlanviewLeanKit Planyo Plivo Podio PollsAPI
    Poloniex Polygon Portainer PortainerToken PositionStack PostageApp Postbacks Postgres PosthogApp Postman
    Postmark Powrbot Prefect Printfection Privacy PrivateKey Processst Prodpad ProspectCRM ProspectIO ProtocolsIO
    ProxyCrawl PubNubPublishKey PubNubSubscriptionKey Pulumi PureStake PushBulletApiKey PusherChannelKey PyPI Qase
    Qualaroo Qubole Quickbase QuickMetrics RabbitMQ RailwayApp Ramp RapidApi Raven Rawg RazorPay Reachmail ReadMe
    ReallySimpleSystems Rebrandly ReCAPTCHA RechargePayments Redbooth RedHatPyxis Redis Refiner Rentman Repairshopr
    Replicate ReplyIO RequestFinance Resend Restpack RestpackHtmlToPdfAPI RestpackScreenshotAPI Rev RevampCRM
    RingCentral Riotgames RiteKit Roaring RobinhoodCrypto RocketReach Rockset Rootly Rosette Route4me Rownd RubyGems
    RunRunIt SaladCloudApiKey Salesblink Salescookie Salesflare Salesforce SalesforceOauth2 SalesforceRefreshToken
    Salesmate Samsara Sanity SatismeterProjectkey SatismeterWritekey SauceLabs ScalewayKey Scalr Scrapeowl
    ScraperAPI ScraperBox ScraperSite ScrapeStack Scrapfly ScrapingAnt ScrapingBee ScrapingDog ScreenshotAPI
    ScreenshotLayer ScrutinizerCi SecurityTrails SegmentApiKey SelectPDF Sellfy Semaphore Sendbird
    SendbirdOrganizationAPI SendGrid SendinBlueV2 Sendoso Sentiment SentryOrgToken SentryToken Serphouse SerpStack
    Sheety Sherpadesk Shipday Shippo ShodanKey ShopeeOpenPlatform Shopify ShopifyOAuth Shortcut Shotstack
    Shutterstock ShutterstockOAuth Signable Signalwire Signaturit Signupgenius Sigopt SimFin Simplesat Simplybook
    SimplyNoted Simvoly SinchMessage Sirv Siteleaf Skrappio SkyBiometry Slack SlackWebhook Smartsheets SmartyStreets
    Smooch SMSApi Snipcart Snowflake SnykKey SolarWindsObservability SonarCloud Sourcegraph SourcegraphCody
    Sparkpost SpectralOps SpeechTextAI SplunkOberservabilityToken Spoonacular SportRadar Sportsmonk SpotifyKey
    SQLServer Square SquareApp Squarespace Squareup SslMate Statuscake Statuspage Statuspal Stitchdata Stockdata
    Storecove Stormboard Stormglass StoryblokAccessToken StoryblokPersonalAccessToken Storychief Strava Streak
    StreamChatMessaging Stripe StripePaymentIntent Stripo Stytch Sugester SumoLogicKey SupabaseToken SuperNotesAPI
    Supportbee Surge SurveyAnyplace SurveyBot SurveySparrow Survicate Swell Swiftype TableauPersonalAccessToken
    Tailscale Tallyfy TatumIO Taxjar Teamgate Teamup TeamViewer TeamworkCRM TeamworkDesk TeamworkSpaces
    TechnicalAnalysisApi Tefter TelegramBotToken Telesign Teletype Telnyx TencentCloudKey
    TerraformCloudPersonalToken Test TestingBot Text2Data Textmagic TheOddsApi Thinkific ThousandEyes TicketMaster
    Tickettailor Tiingo TimeCamp Timekit Timezoneapi TinesWebhook TLy Tmetric Todoist TogglTrack Tokeet TomorrowIO
    Tomtom Tradier Transferwise TravelPayouts TravisCI TrelloApiKey Trimble Tru TrufflehogEnterprise TwelveData
    Twilio TwilioApiKey Twist Twitch TwitchAccessToken Twitter TwitterApiSecret TwitterConsumerkey Tyntec Typeform
    Typetalk UberServerToken Ubidots Uclassify UnifyID Unplugg Unsplash UPCDatabase Uplead UploadCare Uproc
    UptimeRobot Upwave URI Urlscan User Userflow UserStack VagrantCloudPersonalToken VatLayer Vbout Veevavault
    Vercel Verifier Verimail Veriphone VersionEye Viewneo VirusTotal VisualCrossing Voiceflow Voicegain Vonage
    VoodooSMS Vouchery Vpnapi VultrApiKey Vyte Wakatime WalkScore WeatherBit WeatherStack Web3Storage Webengage
    Webex WebexBot Webflow WebScraper Webscraping Websitepulse WeChatAppKey WeightsAndBiases WePay Whoxy Wistia Wit
    Wiz Woopra WordsApi Workday Worksnaps Workstack WorldCoinIndex WorldWeather WpEngine Wrike XAI Yandex Yelp Yext
    YouNeedABudget YouSign YoutubeApiKey ZapierWebhook ZendeskApi ZenkitAPI ZenRows Zenscrape Zenserp Zeplin
    Zerobounce ZeroTier ZipAPI ZipBooks ZipCodeAPI Zipcodebase ZohoCRM ZonkaFeedback ZulipChat
    """.split()  # noqa: SIM905 - 1,068 names; see above
)
OTHER_DETECTOR = "other"

MSG_VERIFICATION = (
    "refused a verification-style option: verified mode sends candidate secrets "
    "to provider APIs and needs an operator decision; this wrapper is offline only"
)
MSG_USAGE = "usage error: unknown option, missing argument or invalid value; see --help"
MSG_TEMP_INSIDE = (
    "refused: the system temp directory is inside the repository or its primary checkout; "
    "set TMPDIR to a directory outside it"
)
MSG_REMOTE_NAME = "refused --remote: not a plain remote name"
MSG_REMOTE_URL = "refused the configured remote URL: only a plain https:// URL without credentials is allowed"
MSG_MIRROR_REMOVAL = "could not remove the temporary mirror (secret-scan-mirror-*); remove it by hand"
MSG_REPORT_LABEL = "full report (owner-only, contains raw values, never paste)"


class ScanError(Exception):
    """A refusal or tool failure; the message is built only from fixed text and integers."""


@dataclass(frozen=True)
class Outputs:
    report_fd: int
    log_fd: int
    # Wrapper-generated file name; the only part of the location ever printed.
    name: str


@dataclass
class Summary:
    """Console-safe totals of a report: closed-set names and integers only."""

    findings: int = 0
    detectors: Counter[str] = field(default_factory=Counter)
    keys: set[str] = field(default_factory=set)
    unknown_keys: int = 0


def _errno_name(exc: OSError) -> str:
    return errno.errorcode.get(exc.errno or 0, "unknown error")


def refuse_verification_options(argv: Sequence[str]) -> None:
    """Reject any option that could turn verification on or widen result types."""
    for token in argv:
        name = token.split("=", 1)[0].lower()
        if name.startswith("-") and any(marker in name for marker in FORBIDDEN_FLAG_MARKERS):
            raise ScanError(MSG_VERIFICATION)


def assert_safe_command(cmd: Sequence[str]) -> None:
    """Last check before TruffleHog runs: offline flags present, no verifier options."""
    options = list(cmd[: cmd.index("--")] if "--" in cmd else cmd)
    missing = [flag for flag in SAFE_FLAGS if flag not in options]
    if missing:
        raise ScanError(f"internal error: unsafe TruffleHog command, missing {missing}")
    refuse_verification_options([part for part in options if part not in {"--no-verification", "--results=unverified"}])


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_SECONDS,
        check=False,
    )
    if result.returncode != 0:
        raise ScanError(f"git {args[0]} failed (exit {result.returncode})")
    return result.stdout


def work_tree_top(repo: Path) -> Path:
    return Path(_git(repo, "rev-parse", "--show-toplevel").strip()).resolve()


def protected_roots(top: Path) -> list[Path]:
    """The scanned work tree, its primary checkout, and this script's checkout."""
    common = Path(_git(top, "rev-parse", "--path-format=absolute", "--git-common-dir").strip())
    return sorted({top, common.resolve().parent, PROJECT_ROOT})


def temp_root(roots: Iterable[Path]) -> Path:
    """The resolved system temp directory, refused when it lies inside a protected root."""
    root = Path(tempfile.gettempdir()).resolve()
    if any(root.is_relative_to(protected) for protected in roots):
        raise ScanError(MSG_TEMP_INSIDE)
    return root


def _mkdtemp(root: Path, prefix: str) -> Path:
    try:
        return Path(tempfile.mkdtemp(prefix=prefix, dir=root))  # 0700, absolute
    except OSError as exc:
        raise ScanError(f"cannot create a private temporary directory ({_errno_name(exc)})") from exc


def _create_private(path: Path) -> int:
    """Create a new owner-only file; never follow a symlink or reuse an existing file."""
    try:
        fd = os.open(path, FILE_FLAGS, 0o600)
    except OSError as exc:
        raise ScanError(f"cannot create output file ({_errno_name(exc)})") from exc
    os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
    return fd


def open_outputs(root: Path, mode: str) -> Outputs:
    """Create the report and the TruffleHog log in a fresh private directory under ``root``."""
    directory = _mkdtemp(root, OUTPUT_PREFIX)
    name = f"{OUTPUT_PREFIX}{mode}-{secrets.token_hex(8)}.jsonl"
    report_fd = _create_private(directory / name)
    try:
        log_fd = _create_private(directory / f"{name}.log")
    except ScanError:
        os.close(report_fd)
        raise
    return Outputs(report_fd, log_fd, name)


def _denied(rel: str) -> bool:
    parts = rel.split("/")
    if DENIED_DIR_PARTS.intersection(parts[:-1]) or parts[-1] in DENIED_DIR_PARTS:
        return True
    return parts[0] == "data" and rel.lower().endswith(DATABASE_SUFFIXES)


def tree_candidates(repo: Path) -> list[str]:
    """Tracked plus untracked-not-ignored regular files, minus denied areas and symlinked paths."""
    listing = _git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    seen: set[str] = set()
    files: list[str] = []
    for rel in listing.split("\0"):
        if not rel or rel in seen or _denied(rel):
            continue
        seen.add(rel)
        path = repo / rel
        # A symlink anywhere on the way (file or parent) could lead outside the tree.
        if os.path.realpath(path) != str(path):
            continue
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue  # deleted or outside a sparse checkout
        if stat.S_ISREG(info.st_mode):
            files.append(rel)
    return files


def batches(paths: Sequence[str], budget: int = TREE_BATCH_BYTES) -> list[list[str]]:
    out: list[list[str]] = []
    current: list[str] = []
    size = 0
    for path in paths:
        cost = len(path.encode()) + 1
        if current and size + cost > budget:
            out.append(current)
            current, size = [], 0
        current.append(path)
        size += cost
    if current:
        out.append(current)
    return out


def _run_trufflehog(cmd: list[str], cwd: Path, out_fd: int, log_fd: int, timeout: int) -> None:
    assert_safe_command(cmd)
    try:
        result = subprocess.run(cmd, cwd=cwd, stdout=out_fd, stderr=log_fd, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ScanError("trufflehog timed out (see --timeout-seconds)") from exc
    except OSError as exc:
        raise ScanError(f"cannot run trufflehog ({_errno_name(exc)})") from exc
    if result.returncode != 0:
        raise ScanError(f"trufflehog exited {result.returncode} (scan error)")


def _exclude_args(repo: Path) -> list[str]:
    ignore = repo / IGNORE_FILE
    return [f"--exclude-paths={ignore}"] if ignore.is_file() else []


def scan_tree(binary: str, repo: Path, out_fd: int, log_fd: int, timeout: int) -> int:
    files = tree_candidates(repo)
    for chunk in batches(files):
        cmd = [binary, "filesystem", *SAFE_FLAGS, *_exclude_args(repo), "--", *chunk]
        _run_trufflehog(cmd, repo, out_fd, log_fd, timeout)
    return len(files)


def validate_remote_url(url: str) -> None:
    """Allow only a plain ``https://host/...`` URL: no option, transport helper or credentials."""
    if not url or len(url) > MAX_REMOTE_URL or not url.startswith("https://"):
        raise ScanError(MSG_REMOTE_URL)
    # Printable ASCII only: no whitespace, control, format or bidi characters.
    if not all("!" <= char <= "~" for char in url):
        raise ScanError(MSG_REMOTE_URL)
    try:
        parts = urllib.parse.urlsplit(url)
        _ = parts.port  # raises ValueError on a malformed port
    except ValueError as exc:
        raise ScanError(MSG_REMOTE_URL) from exc
    if not parts.hostname or "@" in parts.netloc:
        raise ScanError(MSG_REMOTE_URL)


def configured_remote_url(repo: Path, remote: str) -> str:
    """The raw configured URL of ``remote`` (the operand git clone will receive), validated."""
    if not SAFE_REMOTE_NAME.fullmatch(remote):
        raise ScanError(MSG_REMOTE_NAME)
    # NUL-terminated so a newline or other whitespace in the value is validated, not stripped.
    url = _git(repo, "config", "--null", "--get", f"remote.{remote}.url").removesuffix("\0")
    validate_remote_url(url)
    return url


def clone_command(url: str, dest: str) -> list[str]:
    # Public remote: no credential helper may contribute a token. ``--`` ends option parsing.
    return ["git", "-c", "credential.helper=", "clone", "--quiet", "--mirror", "--", url, dest]


def _remove_mirror(mirror_dir: Path, prior: ScanError | None) -> None:
    try:
        shutil.rmtree(mirror_dir)
    except OSError as exc:
        message = f"{prior}; {MSG_MIRROR_REMOVAL}" if prior is not None else MSG_MIRROR_REMOVAL
        raise ScanError(message) from exc


def _clone_and_scan(
    binary: str, url: str, mirror_dir: Path, repo: Path, out_fd: int, log_fd: int, timeout: int
) -> None:
    mirror = mirror_dir / "mirror.git"
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ALLOW_PROTOCOL": CLONE_PROTOCOLS}
    try:
        clone = subprocess.run(
            clone_command(url, str(mirror)),
            cwd=mirror_dir,
            stdout=subprocess.DEVNULL,
            stderr=log_fd,
            env=env,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ScanError("mirror clone timed out (see --timeout-seconds)") from exc
    if clone.returncode != 0:
        raise ScanError(f"mirror clone of the configured remote failed (exit {clone.returncode})")
    cmd = [binary, "git", f"file://{mirror}", "--bare", *SAFE_FLAGS, *_exclude_args(repo)]
    _run_trufflehog(cmd, mirror_dir, out_fd, log_fd, timeout)


def scan_history(binary: str, repo: Path, url: str, root: Path, out_fd: int, log_fd: int, timeout: int) -> None:
    mirror_dir = _mkdtemp(root, MIRROR_PREFIX)
    try:
        _clone_and_scan(binary, url, mirror_dir, repo, out_fd, log_fd, timeout)
    except BaseException as exc:
        _remove_mirror(mirror_dir, exc if isinstance(exc, ScanError) else None)
        raise
    _remove_mirror(mirror_dir, None)


def _detector_name(record: object, number: int) -> str:
    """The DetectorName of a well-formed finding; any other shape is a typed error."""
    error = ScanError(f"unexpected report structure at line {number}")
    if not isinstance(record, dict) or not isinstance(record.get("DetectorName"), str):
        raise error
    metadata = record.get("SourceMetadata")
    data = metadata.get("Data") if isinstance(metadata, dict) else None
    if not isinstance(data, dict) or len(data) != 1 or not isinstance(next(iter(data.values())), dict):
        raise error
    return record["DetectorName"]


def summarize(fh: TextIO) -> Summary:
    """Reduce a JSON Lines report to closed-set names and counts; never keep a field value."""
    summary = Summary()
    unknown: set[str] = set()
    try:
        for number, raw_line in enumerate(fh, start=1):
            if not raw_line.strip():
                continue
            try:
                record = json.loads(raw_line)
            except (ValueError, RecursionError) as exc:
                # Never echo the line: it may hold a secret.
                raise ScanError(f"unparseable JSON at report line {number}") from exc
            name = _detector_name(record, number)
            summary.findings += 1
            summary.detectors[name if name in KNOWN_DETECTORS else OTHER_DETECTOR] += 1
            summary.keys.update(key for key in record if key in REPORT_KEYS)
            unknown.update(key for key in record if key not in REPORT_KEYS)
    except UnicodeDecodeError as exc:
        raise ScanError("the report is not valid UTF-8") from exc
    summary.unknown_keys = len(unknown)
    return summary


def detector_lines(summary: Summary) -> list[str]:
    lines = [f"findings: {summary.findings}"]
    for name, count in sorted(summary.detectors.items(), key=lambda item: (item[0] == OTHER_DETECTOR, item[0])):
        lines.append(f"  {name}: {count}")
    return lines


def key_lines(summary: Summary) -> list[str]:
    lines = [f"keys: {', '.join(sorted(summary.keys))}"]
    if summary.unknown_keys:
        lines.append(f"keys outside the TruffleHog result format: {summary.unknown_keys}")
    return lines


class _FixedErrorParser(argparse.ArgumentParser):
    """argparse whose usage errors never repeat the offending option or value."""

    def error(self, message: str) -> NoReturn:
        del message  # may contain a supplied value
        print(f"secret_scan_local: {MSG_USAGE}", file=sys.stderr)
        raise SystemExit(EXIT_ERROR)


def _int_at_least(minimum: int):
    def parse(text: str) -> int:
        value = int(text)
        if value < minimum:
            raise ValueError
        return value

    return parse


def build_parser() -> argparse.ArgumentParser:
    parser = _FixedErrorParser(
        prog="secret_scan_local.py",
        description=(
            "Run the locally installed TruffleHog offline (no verification) over the working tree or\n"
            "the full public history. The console shows only totals and a count per detector name;\n"
            "nothing taken from a finding (no path, commit or line) is ever printed.\n"
            "Use before a PR that changes credential, identity, transport or hook code and after a\n"
            "suspected leak. Not a CI replacement (CI scans every pushed range) and never verified mode."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/audit/secret_scan_local.py tree\n"
            "  .venv/bin/python scripts/audit/secret_scan_local.py history\n"
            '  .venv/bin/python scripts/audit/secret_scan_local.py show-keys "$REPORT"\n'
            "\n"
            "Fixed TruffleHog flags: " + " ".join(SAFE_FLAGS) + "\n"
            "  plus --exclude-paths=.trufflehogignore when the file exists.\n"
            "\n"
            "Outputs:\n"
            "  Full JSON Lines report (contains RAW secret values) and TruffleHog's log\n"
            "  (<report>.log), both new 0600 files in a new 0700 secret-scan-* directory under the\n"
            "  system temp directory (TMPDIR). Only the generated report file name is printed; find\n"
            '  it with: find "${TMPDIR:-/tmp}" -maxdepth 2 -name <name>. Never paste either file.\n'
            "  stdout: totals and per-detector counts; detector names outside TruffleHog's known set\n"
            "  are counted as 'other'. show-keys prints only a report's top-level key names and\n"
            "  per-detector counts. history: a temporary bare mirror under the system temp\n"
            "  directory, removed afterwards; only a plain https:// remote without credentials.\n"
            "  The run is refused when the system temp directory is inside the repository.\n"
            "\n"
            "Exit codes:\n"
            "  0  no findings (tree, history); report summarized (show-keys)\n"
            "  1  findings (triage per the runbook)\n"
            "  2  refusal, missing trufflehog, git or TruffleHog error, timeout, usage error,\n"
            "     unexpected report structure, mirror removal failure\n"
            "\n"
            "Related: docs/runbooks/secret-scanning.md, .github/workflows/ci.yml (Secret scan),\n"
            "  .trufflehogignore, issue #9416."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=PROJECT_ROOT,
        help="Git work tree to scan or whose remote to mirror (default: this script's checkout).",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=_int_at_least(1),
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Limit per clone or TruffleHog call, in seconds (default: {DEFAULT_TIMEOUT_SECONDS}).",
    )
    sub = parser.add_subparsers(dest="mode", required=True, metavar="{tree,history,show-keys}")
    sub.add_parser(
        "tree",
        help="Scan tracked and untracked-not-ignored files of the work tree "
        "(never .git, .venv, node_modules, .worktrees or data/ databases; symlinks skipped).",
    )
    history = sub.add_parser(
        "history",
        help="Mirror-clone the configured https remote (all refs) and scan every commit with --bare.",
    )
    history.add_argument(
        "--remote",
        default="origin",
        help="Name of the configured public https remote to mirror (default: origin).",
    )
    show_keys = sub.add_parser(
        "show-keys",
        help="Print only the top-level key names of an existing report and its per-detector counts.",
    )
    show_keys.add_argument("report", type=Path, help="A JSON Lines report written by tree or history.")
    return parser


def _show_keys(report: Path) -> int:
    try:
        fh = open(report, encoding="utf-8", errors="strict")  # noqa: SIM115 - closed below
    except OSError as exc:
        raise ScanError(f"cannot open the report ({_errno_name(exc)})") from exc
    with fh:
        if not stat.S_ISREG(os.fstat(fh.fileno()).st_mode):
            raise ScanError("the report is not a regular file")
        summary = summarize(fh)
    for line in (*key_lines(summary), *detector_lines(summary)):
        print(line)
    return EXIT_CLEAN


def _scan(args: argparse.Namespace, binary: str) -> int:
    repo = work_tree_top(args.repo)
    # Refusals come before any output file exists.
    root = temp_root(protected_roots(repo))
    url = configured_remote_url(repo, args.remote) if args.mode == "history" else ""
    outputs = open_outputs(root, args.mode)
    print(
        f"{MSG_REPORT_LABEL}: {outputs.name} in a new secret-scan-* directory under the system temp "
        "directory, log beside it with .log appended"
    )
    try:
        try:
            if args.mode == "tree":
                scanned = scan_tree(binary, repo, outputs.report_fd, outputs.log_fd, args.timeout_seconds)
                print(f"mode: tree, files scanned: {scanned}")
            else:
                scan_history(binary, repo, url, root, outputs.report_fd, outputs.log_fd, args.timeout_seconds)
                print("mode: history")
        except ScanError as exc:
            raise ScanError(f"{exc}; details in the owner-only log beside the report") from exc
        os.lseek(outputs.report_fd, 0, os.SEEK_SET)
        with os.fdopen(os.dup(outputs.report_fd), encoding="utf-8", errors="strict") as fh:
            summary = summarize(fh)
    finally:
        os.close(outputs.report_fd)
        os.close(outputs.log_fd)
    for line in detector_lines(summary):
        print(line)
    return EXIT_FINDINGS if summary.findings else EXIT_CLEAN


def main(argv: Sequence[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    try:
        refuse_verification_options(args_list)
        args = build_parser().parse_args(args_list)
    except ScanError as exc:
        print(f"secret_scan_local: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else EXIT_ERROR
    try:
        if args.mode == "show-keys":
            return _show_keys(args.report)
        binary = shutil.which(TRUFFLEHOG)
        if binary is None:
            print(
                "secret_scan_local: trufflehog not found on PATH; see docs/runbooks/secret-scanning.md",
                file=sys.stderr,
            )
            return EXIT_ERROR
        return _scan(args, binary)
    except ScanError as exc:
        print(f"secret_scan_local: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as exc:  # a traceback could carry report contents or paths
        print(f"secret_scan_local: internal error ({type(exc).__name__})", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
