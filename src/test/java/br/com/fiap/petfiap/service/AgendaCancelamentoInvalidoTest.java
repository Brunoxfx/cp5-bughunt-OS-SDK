package br.com.fiap.petfiap.service;

import br.com.fiap.petfiap.exception.StatusInvalidoException;
import br.com.fiap.petfiap.model.Banho;
import br.com.fiap.petfiap.repository.AtendimentoRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import java.time.LocalDateTime;
import java.util.Optional;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class AgendaCancelamentoInvalidoTest {

    @Mock
    private AtendimentoRepository repository;

    @InjectMocks
    private AgendaService service;

    @Test
    public void deveRecusarCancelamentoQuandoAtendimentoNaoEstiverAgendado() {
        // Arrange: ambos os estados finais devem permanecer intactos.
        String[] estadosFinais = {"CONCLUIDO", "CANCELADO"};
        for (String status : estadosFinais) {
            Banho banho = new Banho(1, "Luna", "PEQUENO", "Joana", LocalDateTime.now().plusDays(1));
            banho.setStatus(status);
            when(repository.findById(1L)).thenReturn(Optional.of(banho));

            // Act + Assert
            assertThrows(StatusInvalidoException.class, () -> service.cancelar(1L));
            assertEquals(status, banho.getStatus());
            verify(repository, never()).save(any());
        }
    }
}
