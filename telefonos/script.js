document.addEventListener('DOMContentLoaded', function() {
    const csvFilePath = 'directorio.csv';
    const userTable = document.getElementById('userTable');
    const loadingMessage = document.getElementById('loadingMessage');

    fetch(csvFilePath)
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al cargar el archivo: ' + response.statusText);
            }
            return response.text();
        })
        .then(csvText => {
            loadingMessage.style.display = 'none';
            
            const rows = csvText.trim().split('\n');
            
            rows.forEach(rowText => {
                if (rowText.trim() === '') return;

                const columns = rowText.split(',');
                if (columns.length === 2) {
                    const userName = columns[0].replace(/"/g, '').trim();
                    const userExtension = columns[1].trim();

                    const newRow = document.createElement('tr');
                    
                    const nameCell = document.createElement('td');
                    nameCell.textContent = userName;
                    
                    const extensionCell = document.createElement('td');
                    extensionCell.textContent = userExtension;
                    
                    newRow.appendChild(nameCell);
                    newRow.appendChild(extensionCell);

                    newRow.style.cursor = 'pointer'; 
                    newRow.addEventListener('click', function() {
                        const textToCopy = `${userName} | Interno: ${userExtension}`;
                        
                        navigator.clipboard.writeText(textToCopy).then(() => {
                            newRow.classList.add('copied');
                            
                            setTimeout(() => {
                                newRow.classList.remove('copied');
                            }, 500);
                        }).catch(err => {
                            console.error('Error al copiar al portapapeles:', err);
                        });
                    });
                    
                    userTable.appendChild(newRow);
                }
            });
        })
        .catch(error => {
            loadingMessage.textContent = 'No se pudo cargar el directorio. Comuníquese al area de SISTEMAS 329.';
            console.error('Error al leer el CSV:', error);
        });
});

const searchInput = document.getElementById('searchInput');

searchInput.addEventListener('input', function() {
    const filter = searchInput.value.toLowerCase();
    const tableRows = document.getElementById('userTable').getElementsByTagName('tr');

    for (let i = 0; i < tableRows.length; i++) {
        let row = tableRows[i];
        let userNameCell = row.getElementsByTagName('td')[0];
        
        if (userNameCell) {
            let userName = userNameCell.textContent || userNameCell.innerText;
            if (userName.toLowerCase().indexOf(filter) > -1) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        }
    }
});
