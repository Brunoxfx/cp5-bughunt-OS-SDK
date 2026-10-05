"""Verifica a API com H2 isolado, sem alterar application.properties."""
import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--esperar-falha-id', action='store_true')
    args = parser.parse_args()
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
    label = 'api-antes-bug12' if args.esperar_falha_id else 'api-final'
    temp = root / 'tmp/validacao'
    temp.mkdir(parents=True, exist_ok=True)
    output = root / 'verificacao/evidencias'
    output.mkdir(parents=True, exist_ok=True)
    checks = []

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

    def schedule(tipo='BANHO', pet='QA-Luna', porte='PEQUENO', date=future):
        return request('POST', params={
            'tipo': tipo, 'petNome': pet, 'porte': porte,
            'tutorNome': 'Tutor de teste', 'dataHora': date.isoformat(),
        })

    command = [java, '-jar', str(jar), f'--server.port={port}', '--server.address=127.0.0.1',
               '--spring.datasource.url=jdbc:h2:mem:petfiap_verificacao',
               '--spring.datasource.driver-class-name=org.h2.Driver',
               '--spring.datasource.username=sa', '--spring.datasource.password=',
               '--spring.jpa.hibernate.ddl-auto=create-drop', '--spring.jpa.show-sql=false']
    with (temp / (label + '.log')).open('w', encoding='utf-8') as log:
        process = subprocess.Popen(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 60
            while True:
                if process.poll() is not None:
                    raise RuntimeError('A API encerrou antes de iniciar; confira o log em tmp/validacao')
                try:
                    request('GET', '/pet/QA-SemRegistro')
                    break
                except (URLError, TimeoutError):
                    if time.monotonic() > deadline:
                        raise RuntimeError('A API nao iniciou em 60 segundos')
                    time.sleep(0.5)

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
                        pet = f'QA-{tipo}-{porte}'
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
                                        ('QA-OutroPet', future, 'Outro pet no mesmo horario permitido')]:
                    status, _ = schedule(pet=pet, date=date)
                    check(status == 201, name)

            evidence = {'banco': 'H2 em memoria', 'configuracao_original_alterada': False,
                        'verificacoes': len(checks), 'falhas': 0, 'cenarios': checks}
            (output / (label + '.json')).write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f'{label}: {len(checks)} verificacoes, 0 falhas')
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == '__main__':
    main()
