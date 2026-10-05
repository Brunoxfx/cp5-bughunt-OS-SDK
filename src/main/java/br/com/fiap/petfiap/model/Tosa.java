package br.com.fiap.petfiap.model;

import jakarta.persistence.Entity;

import java.time.LocalDateTime;

// Tosa: preco por porte, 30 pontos, 60 minutos.
@Entity
public class Tosa extends Atendimento {

    private static final double PRECO_PEQUENO = 70.0;
    private static final double PRECO_MEDIO = 90.0;
    private static final double PRECO_GRANDE = 120.0;
    private static final int PONTOS_FIDELIDADE = 30;
    private static final int DURACAO_MINUTOS = 60;

    public static final String TIPO = "TOSA";

    public Tosa() {
    }

    public Tosa(int protocolo, String petNome, String petPorte, String tutorNome, LocalDateTime dataHora) {
        super(protocolo, petNome, petPorte, tutorNome, dataHora);
    }

    @Override
    public String getTipo() {
        return TIPO;
    }

    @Override
    public double calcularPreco() {
        if ("PEQUENO".equals(getPetPorte())) {
            return PRECO_PEQUENO;
        } else if ("MEDIO".equals(getPetPorte())) {
            return PRECO_MEDIO;
        }
        return PRECO_GRANDE;
    }

    @Override
    public int calcularPontosFidelidade() {
        return PONTOS_FIDELIDADE;
    }

    @Override
    public int getDuracaoMinutos() {
        return DURACAO_MINUTOS;
    }
}
