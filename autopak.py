# Copyright (C) 2019  Matthew James Harrison

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import json
import os
import shutil
import sys
from collections import namedtuple
from hashlib import md5
from zipfile import ZipFile


MOD_DEFINITION_PATH = 'mods.json'
DEPLOY_TARGET = '.'


Mod = namedtuple('Mod', [
    'game_title',
    'mod_title',
    'is_pk4',
    'sources',
    'base_path',
    'game',
    'zip_name',
    'pk4_name',
    'should_deploy',
    'should_install'
])


def get_source_paths(source):
    return [os.path.join(r, f) for r,d,fs in os.walk(source) for f in fs]


def mod_definition_decoder(obj):
    return Mod(
        game_title=obj['game_title'],
        mod_title=obj['mod_title'],
        is_pk4=obj['is_pk4'],
        sources=obj['sources'],
        base_path=obj['base_path'],
        game=obj['game'],
        zip_name=obj['zip_name'],
        pk4_name=obj['pk4_name'],
        should_deploy=obj['should_deploy'],
        should_install=obj['should_install']
    )


def zip_sources(source_data, zip_dir_path, zip_name, zip_type, container_dir=None):
    if not os.path.exists(zip_dir_path):
        os.makedirs(zip_dir_path)
    zip_path = os.path.join(zip_dir_path, zip_name + '.' + zip_type)
    if os.path.exists(zip_path):
        os.remove(zip_path)
    z = ZipFile(zip_path, 'w')
    for source, source_paths in source_data:
        zip_paths = [
            (x, os.path.relpath(x, source))
            for x in source_paths
        ] if not container_dir else [
            (x, os.path.join(container_dir, os.path.relpath(x, source)))
            for x in source_paths
        ]
        for src, arc in zip_paths:
            try:
                z.write(src, arcname=arc)
            except UserWarning:
                pass
    z.close()


def copy_sources(source_data, copy_dir_path):
    for source, source_paths in source_data:
        copy_paths = [
            (x, os.path.join(copy_dir_path, os.path.relpath(x, source)))
            for x in source_paths
        ]
        for src, dst in copy_paths:
            dst_parent = os.path.dirname(dst)
            if not os.path.exists(dst_parent):
                os.makedirs(dst_parent)
            elif os.path.isfile(dst):
                with open(src, 'rb') as f_src, open(dst, 'rb') as f_dst:
                    left = md5(f_src.read()).hexdigest()
                    right = md5(f_dst.read()).hexdigest()
                    if left == right:
                        continue
                os.remove(dst)
            shutil.copy(src, dst)


def display_help():
    print('usage: python autopak.py [install] [deploy] [help]\n')
    print('install  ', 'copies mods into their respective install locations, zipping them into pk4 files as needed')
    print('deploy   ', 'packages mods into zip and pk4 files located in the out/ directory of this project')
    print('help     ', 'displays this screen')


def install(mod):
    destination = os.path.join(mod.base_path, mod.game, 
        mod.pk4_name + '.pk4' if mod.is_pk4 and mod.pk4_name else '')
    print('Installing', mod.mod_title, 'for', mod.game_title, 'to', destination)
    source_data = [
        (source, get_source_paths(source))
        for source in mod.sources
    ]
    if mod.is_pk4:
        zip_sources(source_data, os.path.join(mod.base_path, mod.game), 
            mod.pk4_name, 'pk4')
    else:
        copy_sources(source_data, os.path.join(mod.base_path, mod.game))


def deploy(mod):
    print('Deploying', mod.mod_title, 'for', mod.game_title)
    source_data = [
        (source, get_source_paths(source))
        for source in mod.sources
    ]
    if mod.is_pk4:
        zip_sources(source_data, DEPLOY_TARGET, mod.pk4_name, 'pk4')
    else:
        zip_sources(source_data, DEPLOY_TARGET, mod.zip_name, 'zip',
            container_dir=mod.game)


def main():
    args = sys.argv
    if len(args) != 2:
        display_help()
        sys.exit(1)
    goal = args[1]
    mod_defs = json.loads(open(MOD_DEFINITION_PATH, 'r').read(),
        object_hook=mod_definition_decoder)
    for mod in mod_defs:
        if goal == 'install':
            if mod.should_install:
                install(mod)
        elif goal == 'deploy':
            if mod.should_deploy:
                deploy(mod)
        elif goal == 'help':
            display_help()
            sys.exit(0)
        else:
            print('autopak:\'' + goal + '\'', 'is not a valid command. Run \'autopak help\' using Python 3')
            sys.exit(1)

if __name__ == '__main__':
    main()