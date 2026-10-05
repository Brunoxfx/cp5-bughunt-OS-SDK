import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.Properties;

/** Inspecao somente de leitura; credenciais recebidas pelo ambiente. */
public class OracleInspecao {
    public static void main(String[] args) throws Exception {
        Properties config = new Properties();
        config.setProperty("user", System.getenv("SPRING_DATASOURCE_USERNAME"));
        config.setProperty("password", System.getenv("SPRING_DATASOURCE_PASSWORD"));
        config.setProperty("oracle.net.CONNECT_TIMEOUT", "10000");
        config.setProperty("oracle.jdbc.ReadTimeout", "20000");
        DriverManager.setLoginTimeout(15);
        try (Connection connection = DriverManager.getConnection(System.getenv("SPRING_DATASOURCE_URL"), config);
             Statement statement = connection.createStatement()) {
            boolean exists;
            try (ResultSet result = statement.executeQuery("SELECT COUNT(*) FROM USER_TABLES WHERE TABLE_NAME = 'ATENDIMENTOS'")) {
                result.next();
                exists = result.getInt(1) > 0;
            }
            int rows = 0;
            if (exists) {
                try (ResultSet result = statement.executeQuery("SELECT COUNT(*) FROM ATENDIMENTOS")) {
                    result.next();
                    rows = result.getInt(1);
                }
            }
            StringBuilder columns = new StringBuilder();
            try (ResultSet result = statement.executeQuery(
                    "SELECT COLUMN_NAME, DATA_TYPE FROM USER_TAB_COLUMNS WHERE TABLE_NAME = 'ATENDIMENTOS' ORDER BY COLUMN_ID")) {
                while (result.next()) {
                    if (columns.length() > 0) columns.append(",");
                    columns.append("{\"nome\":\"").append(result.getString(1))
                            .append("\",\"tipo\":\"").append(result.getString(2)).append("\"}");
                }
            }
            boolean identity;
            try (ResultSet result = statement.executeQuery(
                    "SELECT COUNT(*) FROM USER_TAB_IDENTITY_COLS WHERE TABLE_NAME = 'ATENDIMENTOS' AND COLUMN_NAME = 'ID'")) {
                result.next();
                identity = result.getInt(1) > 0;
            }
            System.out.println("{\"conexao\":\"OK\",\"banco\":\"Oracle\",\"versao_principal\":"
                    + connection.getMetaData().getDatabaseMajorVersion() + ",\"tabela_existe\":" + exists
                    + ",\"linhas_existentes\":" + rows + ",\"id_identity\":" + identity
                    + ",\"colunas\":[" + columns + "]}");
        } catch (java.sql.SQLException error) {
            System.out.println("{\"conexao\":\"FALHOU\",\"codigo_oracle\":" + error.getErrorCode() + "}");
            System.exit(1);
        }
    }
}
