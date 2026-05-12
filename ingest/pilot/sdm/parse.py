import yaml
with open('sdm_dp2.yaml', 'r') as infile:
    data = yaml.safe_load(infile)
    for table in data['tables']:
        table_name = table['name']
        print(table_name)
        with open(f'columns/{table_name}', 'w') as outfile:
            for column in table['columnRefs']['base'][table_name]:
                outfile.write(f'{column}\n')
