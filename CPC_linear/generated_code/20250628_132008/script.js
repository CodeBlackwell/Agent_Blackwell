const getDataBtn = document.getElementById('getDataBtn');
const dataDisplay = document.getElementById('dataDisplay');

getDataBtn.addEventListener('click', async () => {
    const response = await fetch('/api/data');
    const data = await response.json();
    dataDisplay.innerText = data.message;
});