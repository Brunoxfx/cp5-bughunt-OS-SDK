package br.com.fiap.petfiap.model;

import org.junit.jupiter.api.Test;
import java.time.LocalDateTime;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class ConsultaPrecoTest {

    @Test
    public void deveCobrar150ReaisQuandoPorteDaConsultaVariar() {
        // Arrange
        String[] portes = {"PEQUENO", "MEDIO", "GRANDE"};
        for (String porte : portes) {
            Atendimento consulta = new ConsultaVeterinaria(1, "Luna", porte, "Joana", LocalDateTime.now().plusDays(1));

            // Act
            double preco = consulta.calcularPreco();

            // Assert
            assertEquals(150.0, preco, 0.001, porte);
        }
    }
}
