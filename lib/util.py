#!/usr/bin/env python3

from os import listdir
from time import time
from pathlib import Path
from hashlib import md5 as md5_hash
from subprocess import Popen as subprocess_popen
from subprocess import PIPE as subprocess_pipe
from json import loads as json_loads
from json import JSONDecodeError

CMD_RELOAD =  'sudo systemctl reload nftables.service'  # has to be changed if no systemd is available
CONFIG = '/etc/nftables.conf'
BASE_DIR = '/etc/nftables.d'
ADDON_DIR = '/etc/nftables.d/addons'
CONFIG_EXT = 'nft'

if not CONFIG_EXT.startswith('.'):
    CONFIG_EXT = f'.{CONFIG_EXT}'

FALLBACK_VAR_VALUE = {
    4: '0.0.0.0',
    6: '::',
}
FILE_TMP_PREFIX = '/tmp/nftables_'
FILE_HEADER = '# Auto-Generated config - DO NOT EDIT MANUALLY!\n\n'


def format_var(name: str, data: list, version: int, append: str = None) -> str:
    if version not in FALLBACK_VAR_VALUE:
        version = 4

    if append not in [None, ' ', '']:
        name = f'{name}_{append}'

    raw = f"define { name } = {{ %s }}"

    if len(data) == 0:
        return raw % FALLBACK_VAR_VALUE[version]

    return raw % ', '.join(map(str, data))


def load_config(file: str, key: str = None) -> (dict, list, None):
    with open(file, 'r', encoding='utf-8') as _cnf:
        try:
            if key is None:
                return json_loads(_cnf.read())

            return json_loads(_cnf.read())[key]

        except JSONDecodeError:
            return None


def _exec(cmd: (str, list)) -> int:
    if isinstance(cmd, str):
        cmd = cmd.split(' ')

    with subprocess_popen(cmd, stdout=subprocess_pipe) as p:
        _ = p.communicate()[0]
        return p.returncode


def _reload() -> bool:
    print('INFO: Reloading NFTables!')
    return _exec(CMD_RELOAD) == 0


def _validate(file: str) -> bool:
    return _exec(['sudo', '/usr/sbin/nft', '-cf', file]) == 0


def _write(file: str, content: str):
    with open(file, 'w', encoding='utf-8') as config:
        config.write(content + '\n\n')

    _exec(['chmod', '640', file])


def _file_hash(file: str) -> str:
    if Path(file).exists():
        with open(file, 'rb') as _c:
            return md5_hash(_c.read()).hexdigest()

    else:
        return md5_hash(b'').hexdigest()


def validate_and_write(key: str, lines: list, file: str):
    file_out = f'{file}{CONFIG_EXT}'
    file_out_path = f'{ADDON_DIR}/{file_out}'
    file_tmp = f'{FILE_TMP_PREFIX}{key}_{time()}{CONFIG_EXT}'
    file_tmp_main = f'{FILE_TMP_PREFIX}main_{time()}{CONFIG_EXT}'
    content = FILE_HEADER + '\n'.join(lines) + '\n'

    _write(file=file_tmp, content=content)

    config_hash = {
        'before': _file_hash(file=file_out_path),
        'after': _file_hash(file=file_tmp),
    }
    config_changed = config_hash['before'] != config_hash['after']

    if config_changed:
        # create config to include existing main-config; must be valid in combination with new one
        addon_includes = ''

        for inc in listdir(ADDON_DIR):
            if inc.endswith(CONFIG_EXT) and inc != file_out:
                addon_includes += f'include "{ADDON_DIR}/{inc}"\n'

        if BASE_DIR not in ['', ' ']:
            addon_includes += f'include "{BASE_DIR}/*{CONFIG_EXT}"\n'

        _write(
            file=file_tmp_main,
            content=f'include "{file_tmp}"\n'
                    f'{addon_includes}\n'
        )

        if _validate(file=file_tmp_main):
            print('INFO: Test-config validated successfully!')
            _write(file=file_out_path, content=content)

            if _validate(file=CONFIG):
                print('INFO: Real-config validated successfully!')
                _reload()

            else:
                raise SystemExit('ERROR: Failed to validate real-config!')

        else:
            raise SystemExit('WARN: Failed to validate test-config!')

        _exec(['rm', file_tmp_main])

    else:
        print('INFO: Config unchanged - nothing to do.')

    _exec(['rm', file_tmp])
