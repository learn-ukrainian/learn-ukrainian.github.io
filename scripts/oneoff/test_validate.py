import yaml, json, jsonschema
schema = json.load(open('schemas/activities-base.schema.json'))
schema_a1 = json.load(open('schemas/activities-a1.schema.json'))
data = yaml.safe_load(open('curriculum/l2-uk-en/a1/activities/stress-and-intonation.yaml'))

resolver = jsonschema.RefResolver.from_schema(schema)
validator = jsonschema.Draft7Validator(schema_a1, resolver=resolver)

for error in validator.iter_errors(data):
    print(error)
