package br.com.fiap.petfiap.service;

import br.com.fiap.petfiap.model.Atendimento;
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
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class AgendaCancelamentoTest {

    @Mock
    private AtendimentoRepository repository;

    @InjectMocks
    private AgendaService service;

    @Test
    public void deveSalvarCancelamentoQuandoAtendimentoEstiverAgendado() {
        // Arrange
        Banho banho = new Banho(1, "Luna", "PEQUENO", "Joana", LocalDateTime.now().plusDays(1));
        when(repository.findById(1L)).thenReturn(Optional.of(banho));
        when(repository.save(banho)).thenReturn(banho);

        // Act
        Atendimento cancelado = service.cancelar(1L);

        // Assert
        assertSame(banho, cancelado);
        assertEquals("CANCELADO", cancelado.getStatus());
        verify(repository).save(banho);
    }
}
