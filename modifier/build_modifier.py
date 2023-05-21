def build_file_updater(new_builds):
    saved_dict = build_file_reader()
    updated_list = saved_dict.get('Builds')
    updated_list.append(new_builds)
    updated_builds = {'Builds': updated_list}
    updated_json = json.dumps(updated_builds, indent=3)
    with open('build_list.json', 'w') as file:
        file.write(updated_json)
    print('updated build list:')
    print(get_json_format())


def add_builds():
    name = input('Build Name: ')
    link = input('Builder Link: ')
    tag = input('Tag: ')
    new_build = {'name': name,
             'link': link,
             'tag': tag}
    build_file_updater(new_build)
