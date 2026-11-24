// The one product switcher shared by every learn-ukrainian Monitor page.
//
// Machinery and Learn Ukrainian are served by this Monitor, so their links are
// relative. The learner site and KubeDojo run on their own local ports; their
// links are built from the current host instead of a hard-coded host name.
(() => {
  const nav = document.getElementById('product-nav');
  if (!nav) return;
  const origin = (port) => `${location.protocol}//${location.hostname}:${port}/`;
  const links = [
    { label: 'Machinery overview', href: '/machinery' },
    { label: 'Fleet & comms', href: '/fleet' },
    { label: 'Subscriptions', href: '/subscriptions' },
    { label: 'Pull requests', href: '/pull-requests' },
    { label: 'Milestones', href: '/milestones' },
    { label: 'Model statistics', href: '/model-stats' },
    { label: 'Learn Ukrainian', href: '/', active: true },
    { label: 'Learner site', href: origin(4321) },
    { label: 'KubeDojo', href: origin(8768) },
  ];
  nav.replaceChildren(...links.map(({ label, href, active }) => {
    const link = document.createElement('a');
    link.href = href;
    link.textContent = label;
    if (active) link.className = 'active';
    return link;
  }));
})();
