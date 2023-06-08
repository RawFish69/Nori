"""
Name: Build modifier
Author: RawFish
Github: https://github.com/RawFish69
Description: To modify build database for Nori
"""

import json


class BuildManager:
    def __init__(self, file_name):
        self.file_name = file_name

    def build_file_generator(self, names=None, links=None, tags=None):
        if names is None:
            names = []
        if links is None:
            links = []
        if tags is None:
            tags = []

        build_list = [{'name': name, 'link': link, 'tag': tag} for name, link, tag in zip(names, links, tags)]
        build_dict = {'Builds': build_list}
        build_json = json.dumps(build_dict, indent=3)
        print(build_json)
        with open(self.file_name, 'w') as file:
            file.write(build_json)
        return build_json

    def build_file_reader(self):
        with open(self.file_name, 'r') as file:
            file_dict = json.load(file)
        return file_dict

    def get_json_format(self):
        with open(self.file_name, 'r') as file:
            file_dict = json.load(file)
        build_json = json.dumps(file_dict, indent=3)
        return build_json

    def build_file_updater(self, new_builds):
        saved_dict = self.build_file_reader()
        updated_list = saved_dict.get('Builds')
        updated_list.append(new_builds)
        updated_builds = {'Builds': updated_list}
        updated_json = json.dumps(updated_builds, indent=3)
        with open(self.file_name, 'w') as file:
            file.write(updated_json)
        print('updated build list:')
        print(self.get_json_format())

    def build_file_search(self, key_word):
        with open(self.file_name, 'r') as file:
            file_dict = json.load(file)
        build_list = file_dict.get('Builds')
        results = [f'**{build["name"]}** [{build["tag"]}]\nLink: {build["link"]}\n' for build in build_list if
                   key_word in build['name'] or key_word in build['tag']]
        print('No results found' if not results else 'Possible match:\n' + '\n'.join(results))

    def add_builds(self):
        name = input('Build Name: ')
        link = input('Builder Link: ')
        tag = input('Tag: ')
        new_build = {'name': name, 'link': link, 'tag': tag}
        self.build_file_updater(new_build)


if __name__ == "__main__":
    bm = BuildManager('build_list.json')
    bm.add_builds()
