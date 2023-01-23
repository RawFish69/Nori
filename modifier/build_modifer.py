import json

def build_file_generator():
    names = []
    links = []
    tags = []
    build_list = []
    for i in range(len(names)):
        build_list.append({'name': names[i], 'link': links[i], 'tag': tags[i]})
    build_dict = {'Builds': build_list}
    build_json = json.dumps(build_dict, indent=3)
    print(build_json)
    with open('build_list.json', 'w') as file:
        file.write(build_json)
    return build_json

def build_file_reader():
    with open('build_list.json', 'r') as file:
        file_dict = json.load(file)
    build_list = file_dict
    return build_list

def get_json_format():
    with open('build_list.json', 'r') as file:
        file_dict = json.load(file)
    build_json = json.dumps(file_dict, indent=3)
    return build_json


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

def build_file_search(key_word):
    with open('build_list.json', 'r') as file:
        file_dict = json.load(file)
    build_list = file_dict.get('Builds')
    result = ''
    for build in build_list:
        name = build.get('name')
        link = build.get('link')
        tag = build.get('tag')
        if key_word in name or key_word in tag:
            result += f'**{name}** [{tag}]\nLink: {link}\n'
        else:
            pass
    if result == '':
        print('No results found')
    else:
        print('Possible match:\n' + result)

def add_builds():
    name = input('Build Name: ')
    link = input('Builder Link: ')
    tag = input('Tag: ')
    new_build = {'name': name,
             'link': link,
             'tag': tag}
    build_file_updater(new_build)

add_builds()
