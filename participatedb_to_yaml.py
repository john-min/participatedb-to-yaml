#! /usr/bin/env python3


# participatedb-to-yaml -- Convert ParticipateDB web site to a Git repository of YAML files
# By: Emmanuel Raviart <emmanuel.raviart@data.gouv.fr>
#
# Copyright (C) 2016 Etalab
# https::#git.framasoft.org/etalab/participatedb-to-yaml
#
# participatedb-to-yaml is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# participatedb-to-yaml is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http:>www.gnu.org/licenses/>.


import argparse
import collections
import os
import sys

import lxml.html
from slugify import slugify
import yaml


# YAML configuration


class folded_str(str):
    pass


class literal_str(str):
    pass


def ordered_dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())


yaml.add_representer(folded_str, lambda dumper, data: dumper.represent_scalar(u'tag:yaml.org,2002:str',
    data, style='>'))
yaml.add_representer(literal_str, lambda dumper, data: dumper.represent_scalar(u'tag:yaml.org,2002:str',
    data, style='|'))
yaml.add_representer(collections.OrderedDict, ordered_dict_representer)
yaml.add_representer(str, lambda dumper, data: dumper.represent_scalar(u'tag:yaml.org,2002:str', data))


#


def add_additional_information(entry_type, entry_id, entry, ul_element):
    assert ul_element.tag == 'ul', 'Unkwown tag {} for ul element in {} {}'.format(
        ul_element.tag, entry_type, entry_id)
    for li_element in ul_element:
        strong_element = li_element[0]
        assert strong_element.tag == 'strong', 'Unkwown tag {} for field name in {} {}'.format(
            strong_element.tag, entry_type, entry_id)
        key = strong_element.text
        if len(li_element) == 1:
            value = strong_element.tail
            entry[key] = value
        else:
            values = []
            for a_element in li_element[1:]:
                assert a_element.tag == 'a', 'Unkwown field format "{}" in {} {}'.format(
                    lxml.html.tostring(li_element, encoding = 'unicode'), entry_type, entry_id)
                if key == 'Category':
                    value = a_element.text
                elif key == 'category':
                    value = a_element.text
                elif key == 'Country':
                    value = a_element.text
                else:
                    assert a_element.attrib['href'] == a_element.text, 'Unkwown field format "{}" in {} {}'.format(
                        lxml.html.tostring(li_element, encoding = 'unicode'), entry_type, entry_id)
                    value = a_element.text
                values.append(value)
            entry[key] = values if len(values) > 1 else values[0]


def add_projects(entry_type, entry_id, h2_element):
    p_element = h2_element.getnext()
    assert p_element.text.startswith('A list of projects'), \
        'Invalid text "{}" in projects of tool {}'.format(p_element.text, entry_id)
    ul_element = p_element.getnext()
    assert ul_element.tag == 'ul', 'Unkwown tag {} for ul element in {} {}'.format(
        ul_element.tag, entry_type, entry_id)
    projects = []
    for li_element in ul_element:
        assert len(li_element) == 1, 'Invalid length for project in {} {}'.format(entry_type, entry_id)
        a_element = li_element[0]
        assert a_element.tag == 'a', 'Unkwown tag {} for project in {} {}'.format(a_element.tag, entry_type, entry_id)
        project = a_element.attrib['href']
        assert project.startswith('/projects/')
        projects.append(int(project.split('/')[-1]))
    return projects


def add_references(entry_type, entry_id, entry, ul_element):
    assert ul_element.tag == 'ul', 'Unkwown tag {} for ul element in {} {}'.format(
        ul_element.tag, entry_type, entry_id)
    references = []
    for li_element in ul_element:
        assert len(li_element) == 1, 'Invalid length for reference in {} {}'.format(entry_type, entry_id)
        a_element = li_element[0]
        assert a_element.tag == 'a', 'Unkwown tag {} for reference in {} {}'.format(a_element.tag, entry_type, entry_id)
        reference = a_element.attrib['href']
        assert reference.startswith('/references/')
        references.append(int(reference.split('/')[-1]))
    if references:
        entry['References'] = references


def add_tools(entry_type, entry_id, h2_element):
    p_element = h2_element.getnext()
    assert p_element.text.startswith('A list of tools'), \
        'Invalid text "{}" in tools of {} {}'.format(p_element.text, entry_type, entry_id)
    ul_element = p_element.getnext()
    assert ul_element.tag == 'ul', 'Unkwown tag {} for ul element in {} {}'.format(
        ul_element.tag, entry_type, entry_id)
    tools = []
    for li_element in ul_element:
        assert len(li_element) == 1, 'Invalid length for tool in {} {}'.format(entry_type, entry_id)
        a_element = li_element[0]
        assert a_element.tag == 'a', 'Unkwown tag {} for tool in {} {}'.format(a_element.tag, entry_type, entry_id)
        tool = a_element.attrib['href']
        assert tool.startswith('/tools/')
        tools.append(int(tool.split('/')[-1]))
    return tools


def create_entry(entry_type, entry_id, entry_div_element):
    assert len(entry_div_element) == 3, "{} {}".format(entry_type, entry_id)
    entry = collections.OrderedDict()
    entry['ID'] = entry_id
    entry['Name'] = entry_div_element.xpath('./h1')[0].text
    description_element = entry_div_element.xpath('./div')[-1]
    description = lxml.html.tostring(description_element, encoding = 'unicode').strip()
    assert description.startswith('<div>')
    assert description.endswith('</div>')
    description = description[len('<div>'):-1 - len('</div>')]
    entry['Description'] = description
    return entry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pages_dir', help = 'path of source directory containing harvested HTML pages')
    parser.add_argument('yaml_dir', help = 'path of target directory for harvested YAML files')
    args = parser.parse_args()

    assert os.path.exists(args.pages_dir)
    if not os.path.exists(args.yaml_dir):
        os.makedirs(args.yaml_dir)

    projects_dir = os.path.join(args.pages_dir, 'projects')
    yaml_dir = os.path.join(args.yaml_dir, 'projects')
    if not os.path.exists(yaml_dir):
        os.makedirs(yaml_dir)
    for filename in os.listdir(projects_dir):
        if not filename.endswith('.html'):
            continue
        entry_id = int(filename.split('.')[0])
        file_path = os.path.join(projects_dir, filename)
        with open(file_path, encoding = 'utf-8') as html_file:
            html = html_file.read()
            html_element = lxml.html.document_fromstring(html)
            projects_div_element = html_element.xpath('//div[@class="projects"]')[0]
            project = create_entry('project', entry_id, projects_div_element)
            for bottomblock_div in html_element.xpath('//div[@class="bottomblock"]'):
                for h2_element in bottomblock_div.xpath('./h2'):
                    block_title = h2_element.text
                    if block_title == 'Additional information':
                        ul_element = h2_element.getnext()
                        add_additional_information('project', entry_id, project, ul_element)
                    elif block_title == 'References':
                        p_element = h2_element.getnext()
                        assert p_element.text.startswith('Additional information'), \
                            'Invalid text "{}" in references of project {}'.format(p_element.text, entry_id)
                        ul_element = p_element.getnext()
                        add_references('project', entry_id, project, ul_element)
                    elif block_title == 'Tools used':
                        ids = add_tools('project', entry_id, h2_element)
                        if ids:
                            project[block_title] = ids
                    else:
                        raise AssertionError('Unkwown title "{}" in project {}'.format(block_title, filename))
            slug = slugify(project['Name'])
            with open(os.path.join(yaml_dir, '{}.yaml'.format(slug)), 'w') as yaml_file:
                yaml.dump(project, yaml_file, allow_unicode = True, default_flow_style = False,
                    indent = 2, width = 120)

    references_dir = os.path.join(args.pages_dir, 'references')
    yaml_dir = os.path.join(args.yaml_dir, 'references')
    if not os.path.exists(yaml_dir):
        os.makedirs(yaml_dir)
    for filename in os.listdir(references_dir):
        if not filename.endswith('.html'):
            continue
        entry_id = int(filename.split('.')[0])
        file_path = os.path.join(references_dir, filename)
        with open(file_path, encoding = 'utf-8') as html_file:
            html = html_file.read()
            html_element = lxml.html.document_fromstring(html)
            references_div_element = html_element.xpath('//div[@class="projects"]')[0]
            reference = create_entry('reference', entry_id, references_div_element)
            for bottomblock_div in html_element.xpath('//div[@class="bottomblock"]'):
                for h2_element in bottomblock_div.xpath('./h2'):
                    block_title = h2_element.text
                    if block_title == 'Additional information':
                        ul_element = h2_element.getnext()
                        add_additional_information('reference', entry_id, reference, ul_element)
                    elif block_title == 'Related projects':
                        ids = add_projects('reference', entry_id, h2_element)
                        if ids:
                            reference[block_title] = ids
                    elif block_title == 'Related tools':
                        ids = add_tools('reference', entry_id, h2_element)
                        if ids:
                            reference[block_title] = ids
                    else:
                        raise AssertionError('Unkwown title "{}" in reference {}'.format(block_title, entry_id))
            slug = slugify(reference['Name'])
            with open(os.path.join(yaml_dir, '{}.yaml'.format(slug)), 'w') as yaml_file:
                yaml.dump(reference, yaml_file, allow_unicode = True, default_flow_style = False,
                    indent = 2, width = 120)

    tools_dir = os.path.join(args.pages_dir, 'tools')
    yaml_dir = os.path.join(args.yaml_dir, 'tools')
    if not os.path.exists(yaml_dir):
        os.makedirs(yaml_dir)
    for filename in os.listdir(tools_dir):
        if not filename.endswith('.html'):
            continue
        entry_id = int(filename.split('.')[0])
        file_path = os.path.join(tools_dir, filename)
        with open(file_path, encoding = 'utf-8') as html_file:
            html = html_file.read()
            html_element = lxml.html.document_fromstring(html)
            tools_div_element = html_element.xpath('//div[@class="tools"]')[0]
            tool = create_entry('tool', entry_id, tools_div_element)
            for bottomblock_div in html_element.xpath('//div[@class="bottomblock"]'):
                for h2_element in bottomblock_div.xpath('./h2'):
                    block_title = h2_element.text
                    if block_title == 'Additional information':
                        ul_element = h2_element.getnext()
                        add_additional_information('tool', entry_id, tool, ul_element)
                    elif block_title == 'Projects':
                        ids = add_projects('tool', entry_id, h2_element)
                        if ids:
                            tool[block_title] = ids
                    elif block_title == 'References':
                        p_element = h2_element.getnext()
                        assert p_element.text.startswith('Additional information'), \
                            'Invalid text "{}" in references of tool {}'.format(p_element.text, entry_id)
                        ul_element = p_element.getnext()
                        add_references('tool', entry_id, tool, ul_element)
                    elif block_title == 'Slice & Dice':
                        next_element = h2_element.getnext()
                        if next_element.tag == 'ul':
                            add_additional_information('tool', entry_id, tool, next_element)
                        elif next_element.tag == 'p':
                            assert next_element.text == 'No categories have been assigned yet.', \
                                'Unkwown text {} for next element in tool {}'.format(next_element.text, entry_id)
                        else:
                            raise AssertionError('Unkwown tag {} for next element in tool {}'.format(
                                next_element.tag, entry_id))
                    else:
                        raise AssertionError('Unkwown title "{}" in tool {}'.format(block_title, entry_id))
            slug = slugify(tool['Name'])
            with open(os.path.join(yaml_dir, '{}.yaml'.format(slug)), 'w') as yaml_file:
                yaml.dump(tool, yaml_file, allow_unicode = True, default_flow_style = False,
                    indent = 2, width = 120)

    return 0


if __name__ == '__main__':
    sys.exit(main())
