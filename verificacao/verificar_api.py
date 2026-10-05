"""Verifica a API com H2 ou Oracle, sem alterar application.properties."""
import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import uuid
import zipfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--esperar-falha-id', action='store_true')
    parser.add_argument('--oracle', action='store_true')
    parser.add_argument('--credenciais', type=Path, help='Arquivo local: usuario/RM e senha, uma linha por campo')
    args = parser.parse_args()
    if args.oracle and args.esperar_falha_id:
        parser.error('A reproducao do bug de ID usa somente H2')
    if args.credenciais and not args.oracle:
        parser.error('--credenciais requer --oracle')
    root = Path(__file__).resolve().parents[1]
    jar = next((root / 'target').glob('petfiap-*.jar'))
    java_home = os.environ.get('JAVA_HOME')
    java = str(Path(java_home) / 'bin/java.exe') if java_home else shutil.which('java')
    if not java:
        raise RuntimeError('Configure JAVA_HOME com JDK 17 ou superior')
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    base = f'http://127.0.0.1:{port}/api/atendimentos'
    label = 'oracle-final' if args.oracle else ('api-antes-bug12' if args.esperar_falha_id else 'api-final')
    temp = root / 'tmp/validacao'
    temp.mkdir(parents=True, exist_ok=True)
    output = root / 'verificacao/evidencias'
    output.mkdir(parents=True, exist_ok=True)
    checks = []
    created_ids = []
    child_env = os.environ.copy()
    prefix = 'QA-CP5-' + uuid.uuid4().hex[:8] + '-' if args.oracle else 'QA-'
    initial_database = None

    def inspect_oracle():
        driver = temp / 'ojdbc.jar'
        with zipfile.ZipFile(jar) as archive:
            name = next(n for n in archive.namelist() if n.startswith('BOOT-INF/lib/ojdbc') and n.endswith('.jar'))
            driver.write_bytes(archive.read(name))
        result = subprocess.run([java, '--class-path', str(driver), str(root / 'verificacao/OracleInspecao.java')],
                                cwd=root, env=child_env, capture_output=True, text=True, timeout=55)
        try:
            data = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            raise RuntimeError('A inspecao Oracle nao retornou um resultado valido') from None
        if result.returncode:
            raise RuntimeError('Conexao Oracle recusada; codigo Oracle: ' + str(data.get('codigo_oracle')))
        return data

    if args.oracle:
        if args.credenciais:
            fields = [line.strip() for line in args.credenciais.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
            if len(fields) != 2:
                parser.error('O arquivo local deve ter usuario/RM e senha em duas linhas')
            child_env['SPRING_DATASOURCE_USERNAME'] = 'rm' + fields[0] if len(fields[0]) == 6 and fields[0].isdigit() else fields[0]
            child_env['SPRING_DATASOURCE_PASSWORD'] = fields[1]
        if not child_env.get('SPRING_DATASOURCE_USERNAME') or not child_env.get('SPRING_DATASOURCE_PASSWORD'):
            parser.error('Forneca --credenciais ou as variaveis locais SPRING_DATASOURCE_USERNAME/PASSWORD')
        child_env['SPRING_DATASOURCE_URL'] = 'jdbc:oracle:thin:@oracle.fiap.com.br:1521:ORCL'
        initial_database = inspect_oracle()
        if initial_database['tabela_existe']:
            required = {'ID', 'DTYPE', 'PROTOCOLO', 'PET_NOME', 'PET_PORTE', 'TUTOR_NOME', 'DATA_HORA', 'STATUS'}
            if not initial_database['id_identity'] or not required.issubset({c['nome'] for c in initial_database['colunas']}):
                raise RuntimeError('Tabela ATENDIMENTOS existente incompativel; nenhum dado foi alterado')
        print('Oracle autenticado; tabela ' + ('existente e compativel' if initial_database['tabela_existe'] else 'ausente'), flush=True)

    def check(condition, name):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    def request(method, path='', params=None):
        url = base + path + ('?' + urlencode(params) if params else '')
        req = Request(url, method=method, data=b'' if method == 'POST' else None)
        try:
            response = urlopen(req, timeout=10)
        except HTTPError as error:
            response = error
        with response:
            body = response.read().decode('utf-8')
            return response.code, json.loads(body) if body else None

    future = (datetime.now() + timedelta(days=365)).replace(microsecond=0)

    def schedule(tipo='BANHO', pet=prefix + 'Luna', porte='PEQUENO', date=future):
        status, item = request('POST', params={
            'tipo': tipo, 'petNome': pet, 'porte': porte,
            'tutorNome': 'Tutor de teste', 'dataHora': date.isoformat(),
        })
        if status == 201:
            created_ids.append(item['id'])
        return status, item

    command = [java, '-jar', str(jar), f'--server.port={port}', '--server.address=127.0.0.1', '--spring.jpa.show-sql=false']
    if args.oracle:
        command += ['--spring.datasource.driver-class-name=oracle.jdbc.OracleDriver',
                    '--spring.jpa.hibernate.ddl-auto=' + ('validate' if initial_database['tabela_existe'] else 'update'),
                    '--spring.jpa.properties.hibernate.hbm2ddl.halt_on_error=true',
                    '--spring.datasource.hikari.connection-timeout=15000']
    else:
        command += ['--spring.datasource.url=jdbc:h2:mem:petfiap_verificacao',
               '--spring.datasource.driver-class-name=org.h2.Driver',
               '--spring.datasource.username=sa', '--spring.datasource.password=',
               '--spring.jpa.hibernate.ddl-auto=create-drop']

    def stop(process):
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def await_ready(process):
        deadline = time.monotonic() + 60
        while True:
            if process.poll() is not None:
                raise RuntimeError('A API encerrou antes de iniciar; confira o log local em tmp/validacao')
            try:
                status, _ = request('GET', '/pet/' + prefix + 'SemRegistro')
                if status == 200:
                    return
            except (URLError, TimeoutError):
                pass
            if time.monotonic() > deadline:
                raise RuntimeError('A API nao iniciou em 60 segundos')
            time.sleep(0.5)

    with (temp / (label + '.log')).open('w', encoding='utf-8') as log:
        process = subprocess.Popen(command, cwd=root, env=child_env, stdout=log, stderr=subprocess.STDOUT)
        try:
            await_ready(process)

            if args.esperar_falha_id:
                status, _ = schedule()
                check(status == 500, 'Cadastro sem geracao de id falha com HTTP 500')
            else:
                items = []
                prices = {'BANHO': [60, 80, 100], 'TOSA': [70, 90, 120], 'CONSULTA': [150, 150, 150]}
                points = {'BANHO': 20, 'TOSA': 30, 'CONSULTA': 50}
                duration = {'BANHO': 45, 'TOSA': 60, 'CONSULTA': 30}
                for tipo in prices:
                    for index, porte in enumerate(['PEQUENO', 'MEDIO', 'GRANDE']):
                        pet = f'{prefix}{tipo}-{porte}'
                        status, item = schedule(tipo, pet, porte)
                        check(status == 201, f'{tipo}/{porte}: cadastro 201')
                        check(isinstance(item['id'], int), f'{tipo}/{porte}: id gerado')
                        check(item['protocolo'] == len(items) + 1, f'{tipo}/{porte}: protocolo sequencial')
                        check(item['status'] == 'AGENDADO' and item['petNome'] == pet
                              and item['petPorte'] == porte and item['tutorNome'] == 'Tutor de teste',
                              f'{tipo}/{porte}: dados preservados')
                        status, summary = request('GET', f"/{item['id']}/resumo")
                        check(status == 200 and summary == {'tipo': tipo, 'preco': prices[tipo][index],
                              'pontosFidelidade': points[tipo], 'duracaoMinutos': duration[tipo]},
                              f'{tipo}/{porte}: preco, pontos e duracao')
                        status, saved = request('GET', f"/{item['id']}")
                        check(status == 200 and saved == item, f'{tipo}/{porte}: leitura persistida')
                        items.append(item)

                first = items[0]
                status, _ = schedule(pet=first['petNome'])
                check(status == 409, 'Mesmo pet e horario agendado: 409')
                status, listed = request('GET', '/pet/' + quote(first['petNome']))
                check(status == 200 and len(listed) == 1, 'Conflito nao salva outro atendimento')
                for kwargs, scenario_label in [({'tipo': 'VACINA'}, 'Tipo inexistente'), ({'pet': ''}, 'Nome ausente'),
                                      ({'porte': ''}, 'Porte ausente'),
                                      ({'date': datetime.now() - timedelta(days=1)}, 'Data passada')]:
                    status, _ = schedule(**kwargs)
                    check(status == 400, scenario_label + ': 400')

                for suffix in ['', '/resumo', '/conclusao', '/cancelamento']:
                    method = 'POST' if suffix in ['/conclusao', '/cancelamento'] else 'GET'
                    status, _ = request(method, '/999999999' + suffix)
                    check(status == 404, 'Id inexistente' + suffix + ': 404')

                status, concluded = request('POST', f"/{first['id']}/conclusao")
                check(status == 200 and concluded['status'] == 'CONCLUIDO', 'Agendado para concluido')
                for operation in ['conclusao', 'cancelamento']:
                    status, _ = request('POST', f"/{first['id']}/{operation}")
                    check(status == 409, 'Concluido recusa ' + operation)
                _, saved = request('GET', f"/{first['id']}")
                check(saved['status'] == 'CONCLUIDO', 'Concluido permanece intacto apos recusas')

                second = items[1]
                status, canceled = request('POST', f"/{second['id']}/cancelamento")
                check(status == 200 and canceled['status'] == 'CANCELADO', 'Agendado para cancelado')
                for operation in ['conclusao', 'cancelamento']:
                    status, _ = request('POST', f"/{second['id']}/{operation}")
                    check(status == 409, 'Cancelado recusa ' + operation)
                _, saved = request('GET', f"/{second['id']}")
                check(saved['status'] == 'CANCELADO', 'Cancelado permanece intacto apos recusas')

                for pet, date, name in [(second['petNome'], future, 'Horario cancelado liberado'),
                                        (first['petNome'], future, 'Horario concluido nao conflita'),
                                        (items[2]['petNome'], future + timedelta(hours=1), 'Outro horario permitido'),
                                        (prefix + 'OutroPet', future, 'Outro pet no mesmo horario permitido')]:
                    status, _ = schedule(pet=pet, date=date)
                    check(status == 201, name)

            persistence = None
            if args.oracle:
                snapshot = {identifier: request('GET', f'/{identifier}')[1] for identifier in created_ids}
                before_restart = inspect_oracle()
                check(before_restart['id_identity'], 'Oracle: IDENTITY confirmado no schema')
                check(before_restart['linhas_existentes'] >= initial_database['linhas_existentes'] + len(created_ids),
                      'Oracle: registros novos confirmados por JDBC')
                print('Cenarios HTTP aprovados; reiniciando a API para conferir persistencia', flush=True)
                stop(process)
                command = [arg.replace('--spring.jpa.hibernate.ddl-auto=update', '--spring.jpa.hibernate.ddl-auto=validate') for arg in command]
                process = subprocess.Popen(command, cwd=root, env=child_env, stdout=log, stderr=subprocess.STDOUT)
                await_ready(process)
                for identifier, previous in snapshot.items():
                    status, current = request('GET', f'/{identifier}')
                    check(status == 200 and current == previous, f'Oracle: atendimento de teste {identifier} preservado apos reinicio')
                after_restart = inspect_oracle()
                check(after_restart['linhas_existentes'] == before_restart['linhas_existentes'],
                      'Oracle: quantidade de registros preservada apos reinicio')
                persistence = {'reinicio_api': True, 'registros_confirmados': len(created_ids),
                               'ids_artificiais': created_ids, 'prefixo_dados_teste': prefix,
                               'linhas_antes': initial_database['linhas_existentes'],
                               'linhas_depois': after_restart['linhas_existentes'],
                               'dados_anteriores_excluidos': False, 'tabela_criada': not initial_database['tabela_existe']}

            evidence = {'banco': 'Oracle FIAP' if args.oracle else 'H2 em memoria', 'configuracao_original_alterada': False,
                        'verificacoes': len(checks), 'falhas': 0, 'cenarios': checks}
            if persistence:
                evidence['persistencia'] = persistence
                evidence['conexao_autenticada'] = True
                evidence['versao_principal'] = initial_database['versao_principal']
            (output / (label + '.json')).write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f'{label}: {len(checks)} verificacoes, 0 falhas')
        finally:
            stop(process)


if __name__ == '__main__':
    main()
