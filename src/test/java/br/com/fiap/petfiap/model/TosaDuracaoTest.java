package br.com.fiap.petfiap.model;

import org.junit.jupiter.api.Test;
import java.time.LocalDateTime;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class TosaDuracaoTest {

    @Test
    public void deveDurar60MinutosQuandoAtendimentoForTosa() {
        // Arrange: a chamada usa o tipo abstrato, como no resumo da API.
        Atendimento tosa = new Tosa(1, "Luna", "MEDIO", "Joana", LocalDateTime.now().plusDays(1));

        // Act
        int duracao = tosa.getDuracaoMinutos();

        // Assert
        assertEquals(60, duracao);
    }
}
