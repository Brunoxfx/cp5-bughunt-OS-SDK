"""Audita arquivos recebidos, testes e commits do Checkpoint 5."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zip-original', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]

    def git(*arguments):
        return subprocess.check_output(['git', *arguments], cwd=root)

    def save(name, value):
        (root / 'verificacao/evidencias' / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

    history = git('log', '--reverse', '--format=%H%x09%s').decode('utf-8').splitlines()
    first_hash, first_message = history[0].split('\t', 1)
    assert first_message == 'chore: estado original do projeto recebido'
    original = {}
    with zipfile.ZipFile(args.zip_original) as archive:
        for info in archive.infolist():
            if not info.is_dir():
                relative = '/'.join(info.filename.split('/')[1:])
                original[relative] = archive.read(info)
    first_files = set(git('ls-tree', '-r', '--name-only', first_hash).decode('utf-8').splitlines())
    assert first_files == set(original), 'Primeiro commit difere dos arquivos do ZIP'
    for path, data in original.items():
        assert git('show', first_hash + ':' + path) == data, 'Arquivo original difere: ' + path

    immutable = [p for p in original if p.startswith('src/test/')]
    immutable += ['pom.xml', 'src/main/resources/application.properties', 'AVALIACAO_README_TEMPLATE.md']
    hashes = {}
    for path in immutable:
        received = original[path]
        current = (root / path).read_bytes()
        assert received == current, 'Arquivo recebido foi alterado: ' + path
        hashes[path] = hashlib.sha256(current).hexdigest()

    categories = [('fix', 'bug', 12, 'src/main/'), ('refactor', 'clean', 6, 'src/main/'),
                  ('test', 'teste', 6, 'src/test/')]
    counts = {}
    cycle = []
    saved_cycle_path = root / 'verificacao/evidencias/ciclo-correcoes.json'
    saved_cycle = {item['item']: item for item in json.loads(saved_cycle_path.read_text(encoding='utf-8'))} if saved_cycle_path.exists() else {}
    for category, label, count, prefix in categories:
        selected = []
        for line in history:
            commit_hash, message = line.split('\t', 1)
            match = re.match(category + ': ' + label + r'(\d{2}) - ', message)
            if not match:
                continue
            selected.append(int(match.group(1)))
            changed = git('diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash).decode('utf-8').splitlines()
            assert changed and all(p.startswith(prefix) for p in changed), message
            if category == 'test':
                assert len(changed) == 1, 'Teste novo deve ter commit proprio'
        assert sorted(selected) == list(range(1, count + 1)), (category, selected)
        counts[category] = len(selected)

    for line in history:
        _, message = line.split('\t', 1)
        match = re.match(r'(?:fix|refactor|test): ((?:bug|clean|teste)\d{2}) - ', message)
        if not match:
            continue
        label = match.group(1)
        evidence = root / 'tmp/validacao' / (label + '.json')
        if evidence.exists():
            result = json.loads(evidence.read_text(encoding='utf-8'))
        elif (root / 'tmp/validacao' / (label + '.log')).exists():
            text = (root / 'tmp/validacao' / (label + '.log')).read_text(encoding='utf-8-sig')
            tests, failures, errors, skipped = re.findall(
                r'Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)', text)[-1]
            result = dict(zip(['tests', 'failures', 'errors', 'skipped'], map(int, [tests, failures, errors, skipped])))
        else:
            result = {key: value for key, value in saved_cycle[label].items() if key not in ['item', 'commit']}
        cycle.append({'item': label, 'commit': message, **result})
    save('ciclo-correcoes.json', cycle)

    suites = [ET.parse(p).getroot() for p in (root / 'target/surefire-reports').glob('TEST-*.xml')]
    summary = {key: sum(int(s.attrib[key]) for s in suites) for key in ['tests', 'failures', 'errors', 'skipped']}
    assert summary == {'tests': 26, 'failures': 0, 'errors': 0, 'skipped': 0}, summary
    build_path = root / 'tmp/validacao/build-final.log'
    if build_path.exists():
        assert 'BUILD SUCCESS' in build_path.read_text(encoding='utf-8-sig')
    else:
        assert json.loads((root / 'verificacao/evidencias/suite-final.json').read_text(encoding='utf-8'))['build'] == 'BUILD SUCCESS'
    save('suite-final.json', {**summary, 'build': 'BUILD SUCCESS', 'comando': 'mvn -B -o verify', 'jdk': 17})
    new_files = [p.relative_to(root).as_posix() for p in (root / 'src/test').rglob('*.java')
                 if p.relative_to(root).as_posix() not in original]
    assert len(new_files) == 6
    assert all((root / path).read_text(encoding='utf-8').count('@Test') == 1 for path in new_files)

    properties = (root / 'src/main/resources/application.properties').read_text(encoding='utf-8')
    assert 'spring.datasource.username=SEU_RM' in properties
    assert 'spring.datasource.password=SUA_SENHA' in properties
    subprocess.run(['git', 'diff', '--check'], cwd=root, check=True)
    api = json.loads((root / 'verificacao/evidencias/api-final.json').read_text(encoding='utf-8'))
    assert api['falhas'] == 0 and api['verificacoes'] >= 70
    audit = {'primeiro_commit': first_hash, 'arquivos_originais_no_primeiro_commit': len(original),
             'primeiro_commit_identico_ao_zip': True, 'arquivos_testes_originais_intactos': 7,
             'testes_originais': 20, 'testes_novos': 6, 'commits_por_categoria': counts,
             'pom_original_intacto': True, 'application_properties_original_intacto': True,
             'credenciais': 'SEU_RM/SUA_SENHA', 'sha256_arquivos_preservados': hashes,
             'suite_final': summary, 'api_h2': {'verificacoes': api['verificacoes'], 'falhas': api['falhas']},
             'publicacao_github': 'pendente', 'entrega_teams': 'pendente'}
    save('auditoria-entrega.json', audit)
    print('Auditoria concluida: original preservado, 12 fixes, 6 refactors, 6 testes novos e suite 26/26.')


if __name__ == '__main__':
    main()
