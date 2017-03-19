# python3.6 required
import argparse
import datetime
import glob
import json
import os
import shutil
import textwrap


BASE_PATH = 'Plugins'


def _create_uplugin(path, project_name):
    print(f'Creating {project_name}.uplugin')
    ts = datetime.datetime.utcnow().isoformat()
    uplugin = {
        'FileVersion': 3,
        'VersionName': ts,
        'FriendlyName': project_name,
        'EnabledByDefault': True,
        'Modules': [
            {
                'Name': f'{project_name}',
                'Type': 'Runtime',
            },
        ],
    }

    with open(f'{project_name}.uplugin', 'w') as fp:
        json.dump(uplugin, fp, indent=4)


def _create_public(path, project_name):
    public = os.path.join('Source', project_name, 'Public')

    os.mkdir(public)

    header = os.path.join(public, f'I{project_name}.h')
    print(f'Creating {header}')
    with open(header, 'w') as fp:
        fp.write(textwrap.dedent(f'''
            #pragma once

            #include "ModuleManager.h"

            class I{project_name} : public IModuleInterface {{
                public:
                    static inline I{project_name}& Get() {{
                        return FModuleManager::LoadModuleChecked<I{project_name}>("{project_name}");
                    }}

                    static inline bool IsAvailable() {{
                        return FModuleManager::Get().IsModuleLoaded("{project_name}");
                    }}
            }};
            ''',
        ))


def _create_private(path, project_name):
    source = os.path.join('Source', project_name)
    private = os.path.join(source, 'Private')

    os.mkdir(private)

    # create empty pre-compiled header
    open(os.path.join(private, f'{project_name}PrivatePCH.h'), 'w').close()

    cpp = os.path.join(private, f'{project_name}.cpp')
    print(f'Creating {cpp}')
    with open(cpp, 'w') as fp:
        fp.write(textwrap.dedent(f'''
            #include "{project_name}PrivatePCH.h"
            #include "I{project_name}.h"

            class F{project_name} : public I{project_name} {{
                virtual void StartupModule() override;
                virtual void ShutdownModule() override;

            }};

            IMPLEMENT_MODULE(F{project_name}, {project_name})

            void F{project_name}::StartupModule() {{}}

            void F{project_name}::ShutdownModule() {{}}
            ''',
        ))

    source = os.path.join(path, source)

    for cpp in glob.iglob(os.path.join(source, '*.cpp')):
        filename = os.path.basename(cpp)
        if os.path.splitext(filename)[0] != project_name:
            dest = os.path.join(private, filename)
            print(f'Creating {dest}')
            with open(dest, 'w') as w:
                w.write(f'#include "{project_name}PrivatePCH.h"\n')
                with open(cpp, 'r') as r:
                    shutil.copyfileobj(r, w)


def _create_classes(path, project_name):
    source = os.path.join('Source', project_name)
    classes = os.path.join(source, 'Classes')

    os.mkdir(classes)

    source = os.path.join(path, source)

    for header in glob.iglob(os.path.join(source, '*.h')):
        filename = os.path.basename(header)
        dest = os.path.join(classes, filename)
        print(f'Creating {dest}')
        shutil.copyfile(header, dest)


def _create_source(path, project_name):
    source = os.path.join('Source', project_name)

    os.makedirs(source)

    build = os.path.join(source, f'{project_name}.Build.cs')
    print(f'Creating {build}')
    shutil.copyfile(os.path.join(path, build), build)

    _create_public(path, project_name)
    _create_private(path, project_name)
    _create_classes(path, project_name)


def _create_third_party(path):
    third_party = 'ThirdParty'
    source = os.path.join(path, third_party)
    if os.path.isdir(source):
        print(f'Creating {third_party}')
        shutil.copytree(source, third_party)


def project2plugin(path):
    abspath = os.path.abspath(path)
    project_name = os.path.basename(abspath)
    wd = os.path.join(BASE_PATH, project_name)

    shutil.rmtree(wd, ignore_errors=True)
    os.makedirs(wd)
    os.chdir(wd)

    _create_uplugin(path, project_name)
    _create_source(path, project_name)
    _create_third_party(path)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('path')

    return parser.parse_args()


def main():
    args = _parse_args()

    project2plugin(args.path)


if __name__ == '__main__':
    main()
