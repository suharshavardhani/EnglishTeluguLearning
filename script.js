let allWords = [];
let filteredWords = [];
let currentPage = 1;
const pageSize = 50; // Renders 50 cards per page to maintain high performance across 10,000 records

document.addEventListener('DOMContentLoaded', () => {
  fetchWords();

  document.getElementById('search-input').addEventListener('input', handleSearch);
  document.getElementById('prev-btn').addEventListener('click', () => changePage(-1));
  document.getElementById('next-btn').addEventListener('click', () => changePage(1));
});

async function fetchWords() {
  try {
    const response = await fetch('words.json');
    if (!response.ok) throw new Error('Failed to load JSON');
    allWords = await response.json();
    filteredWords = [...allWords];
    
    document.getElementById('total-count').innerText = `${allWords.length.toLocaleString()} Words`;
    renderPage();
  } catch (error) {
    console.error('Error loading words:', error);
    document.getElementById('words-container').innerHTML = `
      <p style="color: #ef4444; grid-column: 1/-1;">
        Could not load words.json. Make sure words.json exists in the root folder.
      </p>`;
  }
}

function renderPage() {
  const container = document.getElementById('words-container');
  container.innerHTML = '';

  const totalPages = Math.ceil(filteredWords.length / pageSize) || 1;
  if (currentPage > totalPages) currentPage = totalPages;
  if (currentPage < 1) currentPage = 1;

  const startIndex = (currentPage - 1) * pageSize;
  const pageItems = filteredWords.slice(startIndex, startIndex + pageSize);

  if (pageItems.length === 0) {
    container.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: var(--text-muted);">No matching words found.</p>`;
  } else {
    pageItems.forEach((item, index) => {
      const globalIndex = startIndex + index + 1;
      const card = document.createElement('div');
      card.className = 'word-card';
      card.innerHTML = `
        <div class="card-header">
          <span class="word-title">${escapeHtml(item.word)}</span>
          <span class="word-index">#${globalIndex}</span>
        </div>
        <div class="meaning-box">
          <div class="meaning-label">తెలుగు అర్థం</div>
          <div class="telugu-text">${escapeHtml(item.meaning || item.telugu_meaning || '')}</div>
        </div>
        ${item.example ? `
          <div class="example-box">
            <strong>Example:</strong> ${escapeHtml(item.example)}
          </div>
        ` : ''}
        ${item.telugu_example ? `
          <div class="example-box">
            <strong>ఉదాహరణ:</strong> ${escapeHtml(item.telugu_example)}
          </div>
        ` : ''}
      `;
      container.appendChild(card);
    });
  }

  document.getElementById('page-info').innerText = `Page ${currentPage} of ${totalPages}`;
  document.getElementById('prev-btn').disabled = currentPage === 1;
  document.getElementById('next-btn').disabled = currentPage === totalPages || totalPages === 0;
}

function handleSearch(event) {
  const query = event.target.value.toLowerCase().trim();
  filteredWords = allWords.filter(item => {
    const wordMatch = item.word && item.word.toLowerCase().includes(query);
    const meaningMatch = (item.meaning || item.telugu_meaning || '').toLowerCase().includes(query);
    return wordMatch || meaningMatch;
  });
  currentPage = 1;
  renderPage();
}

function changePage(delta) {
  currentPage += delta;
  renderPage();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
