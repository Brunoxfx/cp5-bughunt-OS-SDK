package br.com.fiap.petfiap.model;

import org.junit.jupiter.api.Test;
import java.time.LocalDateTime;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class BanhoPrecoTest {

    @Test
    public void deveCobrarPrecoDaTabelaQuandoPorteVariar() {
        // Arrange
        String[] portes = {"PEQUENO", "MEDIO", "GRANDE"};
        double[] precosEsperados = {60.0, 80.0, 100.0};

        for (int i = 0; i < portes.length; i++) {
            Atendimento banho = new Banho(1, "Luna", portes[i], "Joana", LocalDateTime.now().plusDays(1));

            // Act
            double preco = banho.calcularPreco();

            // Assert
            assertEquals(precosEsperados[i], preco, 0.001, portes[i]);
        }
    }
}
