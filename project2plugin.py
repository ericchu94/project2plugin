# python3.6 required
import argparse
import datetime
import glob
import json
import os
import shutil
import textwrap


BASE_PATH = 'Plugins'
BINARIES = ['dll', 'pdb']
MODULES = 'UE4Editor.modules'


def _create_dir(wd):
    os.makedirs(wd, exist_ok=True)


def _create_uplugin(path, project_name):
    uplugin = {
        'FileVersion': 3,
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


def _create_binaries(path, project_name):
    binaries = os.path.join('Binaries', 'Win64')

    os.makedirs(binaries)

    modules_path = os.path.join(path, binaries, MODULES)
    shutil.copy(modules_path, binaries)
    with open(modules_path, 'r') as fp:
        modules = json.load(fp)
        binary_name = os.path.splitext(modules['Modules'][project_name])[0]
        for binary in BINARIES:
            binary_path = os.path.join(
                path,
                binaries,
                f'{binary_name}.{binary}',
            )
            shutil.copy(binary_path, binaries)


def _create_public(path, project_name):
    public = os.path.join('Source', project_name, 'Public')

    os.mkdir(public)

    header = os.path.join(public, f'I{project_name}.h')
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
            with open(os.path.join(private, filename), 'w') as w:
                w.write(f'#include "{project_name}PrivatePCH.h"\n')
                with open(cpp, 'r') as r:
                    w.write(r.read())


def _create_classes(path, project_name):
    source = os.path.join('Source', project_name)
    classes = os.path.join(source, 'Classes')

    os.mkdir(classes)

    source = os.path.join(path, source)

    for header in glob.iglob(os.path.join(source, '*.h')):
        #if os.path.splitext(os.path.basename(header))[0] != project_name:
            shutil.copy(header, classes)


def _create_source(path, project_name):
    source = os.path.join('Source', project_name)

    os.makedirs(source)

    build = os.path.join(path, source, f'{project_name}.Build.cs')
    shutil.copy(build, source)

    _create_public(path, project_name)
    _create_private(path, project_name)
    _create_classes(path, project_name)
    


def project2plugin(path):
    abspath = os.path.abspath(path)
    project_name = os.path.basename(abspath)
    ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    wd = os.path.join(BASE_PATH, f'{project_name}-{ts}')
    
    _create_dir(wd)

    os.chdir(wd)

    _create_uplugin(path, project_name)
    #_create_binaries(path, project_name)
    _create_source(path, project_name)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('path')

    return parser.parse_args()


def main():
    args = _parse_args()

    project2plugin(args.path)


if __name__ == '__main__':
    main()
