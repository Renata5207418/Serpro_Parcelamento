        // Dicionário de serviço para cada id_sistema
        const servicoOptions = {
            "PARCSN": "GERARDAS161",
            "PARCSN-ESP": "GERARDAS171",
            "PERTSN": "GERARDAS181",
            "RELPSN": "GERARDAS191",
            "PARCMEI": "GERARDAS201",
            "PARCMEI-ESP": "GERARDAS211",
            "PERTMEI": "GERARDAS221",
            "RELPMEI": "GERARDAS231"
        };

        function updateServicoOptions() {
            const sistemaSelect = document.getElementById("id_sistema");
            const servicoInput = document.getElementById("id_servico");
            const selectedSistema = sistemaSelect.value;

            // Preencher automaticamente o campo "id_servico"
            if (selectedSistema && servicoOptions[selectedSistema]) {
                servicoInput.value = servicoOptions[selectedSistema];
            } else {
                servicoInput.value = '';
            }
        }

        // Máscara para Ano e Mês da Parcela (AAAAMM)
        const parcelaMask = IMask(document.getElementById('parcela_para_emitir'), {
            mask: '000000' // Para formato AAAAMM
        });

     // Envio do formulário usando JavaScript para evitar redirecionamento
    document.getElementById("dasForm").addEventListener("submit", function(event) {
        event.preventDefault(); // Evita o redirecionamento padrão do formulário

        const formData = new FormData(this);
        const successMessage = document.getElementById("successMessage");
        let errorMessage = document.getElementById("errorMessage");

        // Remover qualquer mensagem existente
        successMessage.style.display = "none";
        if (errorMessage) {
            errorMessage.remove(); // Remover mensagem de erro antiga
        }

        fetch('/gerar_das', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (status === 200) {
                successMessage.style.display = "block"; // Mostrar mensagem de sucesso
                this.reset(); // Limpar o formulário para novo envio
            } else {
                // Criar uma nova div para a mensagem de erro
                errorMessage = document.createElement("div");
                errorMessage.id = "errorMessage";
                errorMessage.className = "alert alert-danger mt-3";
                errorMessage.role = "alert";

                // Mostrar a mensagem específica do erro, se houver
                if (body.mensagem) {
                    errorMessage.innerText = Erro ao enviar: ${body.mensagem};
                } else if (body.error) {
                    errorMessage.innerText = Erro ao enviar: ${body.error};
                } else {
                    errorMessage.innerText = "Erro ao enviar. Por favor, tente novamente.";
                }

                this.insertAdjacentElement('beforebegin', errorMessage);
            }
        })
        .catch(error => {
            console.error("Erro ao enviar o formulário:", error);
            // Criar uma nova div para a mensagem de erro
            errorMessage = document.createElement("div");
            errorMessage.id = "errorMessage";
            errorMessage.className = "alert alert-danger mt-3";
            errorMessage.role = "alert";
            errorMessage.innerText = "Erro ao enviar. Por favor, tente novamente.";
            this.insertAdjacentElement('beforebegin', errorMessage);
        });
        });

    // Envio em Lote
    document.getElementById("batchUploadForm").addEventListener("submit", function(event) {
        event.preventDefault(); // Evitar envio padrão

        const formData = new FormData(this);
        const batchMessage = document.getElementById("batchSuccessMessage");
        const detailedMessage = document.getElementById("batchDetailedMessage");
        const batchSubmitButton = document.getElementById("batchSubmitButton");

        // Mostrar mensagem de progresso e desabilitar botão
        batchMessage.style.display = "block";
        batchMessage.classList.remove("alert-success", "alert-danger");
        batchMessage.classList.add("alert-info");
        batchMessage.innerText = "Envio em lote em andamento. Por favor, aguarde...";
        detailedMessage.style.display = "none";
        batchSubmitButton.disabled = true;

        fetch('/enviar_em_lote', {
            method: 'POST',
            body: formData
        }).then(response => {
            if (!response.ok) {
                throw new Error("Erro ao enviar o arquivo.");
            }
            return response.json();
        })
        .then(data => {
            batchMessage.classList.remove("alert-info");

            if (data.message === "Envio em lote concluído") {
                batchMessage.classList.add("alert-success");
                batchMessage.innerText = "Envio em lote concluído com sucesso!";

                let detalhes = "<b>Resumo do envio:</b><br>";
                data.resultados.forEach(result => {
                    detalhes += <strong>CNPJ:</strong> ${result.CNPJ} - <strong>Status:</strong> ${result.status} - <strong>Mensagem:</strong> ${result.mensagem}<br>;
                });

                detailedMessage.innerHTML = detalhes;
                detailedMessage.style.display = "block";
            } else {
                batchMessage.classList.add("alert-danger");
                batchMessage.innerText = "Erro ao iniciar o envio em lote.";
                detailedMessage.innerHTML = "";
                detailedMessage.style.display = "none";
            }
        })
        .catch(error => {
            console.error("Erro ao enviar o arquivo:", error);
            batchMessage.classList.remove("alert-info");
            batchMessage.classList.add("alert-danger");
            batchMessage.innerText = "Erro ao enviar o arquivo. Verifique os detalhes abaixo.";

            detailedMessage.innerHTML = "Não foi possível iniciar o envio. Verifique o arquivo e tente novamente.";
            detailedMessage.style.display = "block";
        })
        .finally(() => {
            batchSubmitButton.disabled = false; // Reabilitar botão
        });
    });