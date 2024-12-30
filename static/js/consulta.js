 function filtrar() {
            const contribuinte = document.querySelector('input[name="contribuinte"]').value;
            const mes = document.querySelector('select[name="mes"]').value;

            let queryString = "/consulta?";
            if (contribuinte) {
                queryString += contribuinte=${contribuinte}&;
            }
            if (mes) {
                queryString += mes=${mes}&;
            }

            window.location.href = queryString;
        }

        // Função para baixar todos os PDFs em lote
        function baixarTodos() {
            window.location.href = '/baixar_todos_recibos';
        }