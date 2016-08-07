#! /usr/bin/env python3


# participatedb-to-yaml -- Convert ParticipateDB web site to a Git repository of YAML files
# By: Emmanuel Raviart <emmanuel.raviart@data.gouv.fr>
#
# Copyright (C) 2016 Etalab
# https://git.framasoft.org/codegouv/participatedb-to-yaml
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


"""Harvest HTML pages from ParticipateDB.com."""


import argparse
import os
import sys
import urllib.parse
import urllib.request

import lxml.html


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pages_dir', help = 'path of target directory for harvested HTML pages')
    args = parser.parse_args()

    if not os.path.exists(args.pages_dir):
        os.makedirs(args.pages_dir)

    site_url = "http://www.participatedb.com/"

    page_number = 1
    projects_path = []
    while True:
        page_url = urllib.parse.urljoin(site_url, "/projects/?page={}".format(page_number))
        response = urllib.request.urlopen(page_url)
        html = response.read().decode("utf-8")
        html_element = lxml.html.document_fromstring(html)
        a_elements = html_element.xpath('//ul[@class="plainlist"]/li/a')
        if not a_elements:
            break
        for a_element in a_elements:
            projects_path.append(a_element.attrib['href'])
        page_number += 1
    print("{} projects found.".format(len(projects_path)))

    projects_dir = os.path.join(args.pages_dir, 'projects')
    if not os.path.exists(projects_dir):
        os.makedirs(projects_dir)

    for project_path in projects_path:
        page_url = urllib.parse.urljoin(site_url, project_path)
        response = urllib.request.urlopen(page_url)
        html = response.read().decode("utf-8")
        project_number = project_path.split('/')[-1]
        page_path = os.path.join(projects_dir, '{}.html'.format(project_number))
        with open(page_path, 'w', encoding = 'utf-8') as page_file:
            page_file.write(html)

    page_number = 1
    references_path = []
    while True:
        page_url = urllib.parse.urljoin(site_url, "/references/?page={}".format(page_number))
        response = urllib.request.urlopen(page_url)
        html = response.read().decode("utf-8")
        html_element = lxml.html.document_fromstring(html)
        a_elements = html_element.xpath('//ul[@class="plainlist"]/li/a')
        if not a_elements:
            break
        for a_element in a_elements:
            references_path.append(a_element.attrib['href'])
        page_number += 1
    print("{} references found.".format(len(references_path)))

    references_dir = os.path.join(args.pages_dir, 'references')
    if not os.path.exists(references_dir):
        os.makedirs(references_dir)

    for reference_path in references_path:
        page_url = urllib.parse.urljoin(site_url, reference_path)
        response = urllib.request.urlopen(page_url)
        html = response.read().decode("utf-8")
        reference_number = reference_path.split('/')[-1]
        page_path = os.path.join(references_dir, '{}.html'.format(reference_number))
        with open(page_path, 'w', encoding = 'utf-8') as page_file:
            page_file.write(html)

    page_number = 1
    tools_path = []
    while True:
        page_url = urllib.parse.urljoin(site_url, "/tools/?page={}".format(page_number))
        response = urllib.request.urlopen(page_url)
        html = response.read().decode("utf-8")
        html_element = lxml.html.document_fromstring(html)
        a_elements = html_element.xpath('//ul[@class="plainlist"]/li/a')
        if not a_elements:
            break
        for a_element in a_elements:
            tools_path.append(a_element.attrib['href'])
        page_number += 1
    print("{} tools found.".format(len(tools_path)))

    tools_dir = os.path.join(args.pages_dir, 'tools')
    if not os.path.exists(tools_dir):
        os.makedirs(tools_dir)

    for tool_path in tools_path:
        page_url = urllib.parse.urljoin(site_url, tool_path)
        response = urllib.request.urlopen(page_url)
        html = response.read().decode("utf-8")
        tool_number = tool_path.split('/')[-1]
        page_path = os.path.join(tools_dir, '{}.html'.format(tool_number))
        with open(page_path, 'w', encoding = 'utf-8') as page_file:
            page_file.write(html)

    return 0


if __name__ == '__main__':
    sys.exit(main())
