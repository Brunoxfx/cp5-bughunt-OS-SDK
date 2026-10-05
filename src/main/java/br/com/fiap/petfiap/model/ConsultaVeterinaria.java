package br.com.fiap.petfiap.model;

import jakarta.persistence.Entity;

import java.time.LocalDateTime;

// Consulta veterinaria: preco fixo (independe do porte), 50 pontos, 30 minutos.
@Entity
public class ConsultaVeterinaria extends Atendimento {

    private static final double PRECO_FIXO = 150.0;
    private static final int PONTOS_FIDELIDADE = 50;

    public static final String TIPO = "CONSULTA";

    public ConsultaVeterinaria() {
    }

    public ConsultaVeterinaria(int protocolo, String petNome, String petPorte, String tutorNome, LocalDateTime dataHora) {
        super(protocolo, petNome, petPorte, tutorNome, dataHora);
    }

    @Override
    public String getTipo() {
        return TIPO;
    }

    @Override
    public double calcularPreco() {
        return PRECO_FIXO;
    }

    @Override
    public int calcularPontosFidelidade() {
        return PONTOS_FIDELIDADE;
    }
}
