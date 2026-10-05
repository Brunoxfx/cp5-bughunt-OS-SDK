package br.com.fiap.petfiap.model;

import jakarta.persistence.Entity;

import java.time.LocalDateTime;

// Banho: preco por porte, 20 pontos, 45 minutos.
@Entity
public class Banho extends Atendimento {

    private static final double PRECO_PEQUENO = 60.0;
    private static final double PRECO_MEDIO = 80.0;
    private static final double PRECO_GRANDE = 100.0;
    private static final int PONTOS_FIDELIDADE = 20;
    private static final int DURACAO_MINUTOS = 45;

    public static final String TIPO = "BANHO";

    public Banho() {
    }

    public Banho(int protocolo, String petNome, String petPorte, String tutorNome, LocalDateTime dataHora) {
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
