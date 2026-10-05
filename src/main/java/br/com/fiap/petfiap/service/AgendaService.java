package br.com.fiap.petfiap.service;

import br.com.fiap.petfiap.exception.AtendimentoNaoEncontradoException;
import br.com.fiap.petfiap.exception.HorarioOcupadoException;
import br.com.fiap.petfiap.model.Atendimento;
import br.com.fiap.petfiap.repository.AtendimentoRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

// Regras de agenda do PetFiap: agendar, concluir e cancelar atendimentos.
@Service
public class AgendaService {

    @Autowired
    private AtendimentoRepository repository;

    // Agenda um novo atendimento: recusa horario ja ocupado pelo mesmo pet.
    public Atendimento agendar(Atendimento novoAtendimento) {
        if (novoAtendimento.getDataHora() == null || novoAtendimento.getDataHora().isBefore(LocalDateTime.now())) {
            throw new IllegalArgumentException("Data e hora devem estar no presente ou futuro");
        }
        List<Atendimento> atendimentosDoPet = repository.findByPetNome(novoAtendimento.getPetNome());
        for (Atendimento atendimentoExistente : atendimentosDoPet) {
            if (atendimentoExistente.getPetNome().equals(novoAtendimento.getPetNome()) && atendimentoExistente.getDataHora().equals(novoAtendimento.getDataHora())
                    && "AGENDADO".equals(atendimentoExistente.getStatus())) {
                throw new HorarioOcupadoException(
                        "Pet " + novoAtendimento.getPetNome() + " ja possui atendimento agendado nesse horario");
            }
        }
        Atendimento salvo = repository.save(novoAtendimento);
        return salvo;
    }

    // Busca pelo id; nunca retorna null, o orElseThrow garante a excecao.
    public Atendimento buscarPorId(Long id) {
        return repository.findById(id)
                .orElseThrow(() -> new AtendimentoNaoEncontradoException("Atendimento nao encontrado: " + id));
    }

    // Conclui o atendimento (status AGENDADO -> CONCLUIDO).
    public Atendimento concluir(Long id) {
        Atendimento atendimento = buscarPorId(id);
        atendimento.concluir();
        return repository.save(atendimento);
    }

    // Cancela o atendimento (status AGENDADO -> CANCELADO).
    public Atendimento cancelar(Long id) {
        Atendimento atendimento = buscarPorId(id);
        atendimento.cancelar();
        return repository.save(atendimento);
    }

    public List<Atendimento> buscarPorPet(String petNome) {
        return repository.findByPetNome(petNome);
    }
}
