package br.com.fiap.petfiap.apresentacao;

import br.com.fiap.petfiap.model.Atendimento;

public class ReciboAgendamento {

    public static void imprimir(Atendimento atendimento) {
        System.out.println("Recibo: atendimento " + atendimento.getProtocolo()
                + " agendado para " + atendimento.getPetNome() + " (tutor " + atendimento.getTutorNome() + ")");
    }
}
