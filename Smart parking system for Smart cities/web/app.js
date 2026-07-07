const state = { data: null, selectedSlot: null };
const $ = (selector) => document.querySelector(selector);

async function api(path, options = {}) {
  const response = await fetch(path, {headers: {'Content-Type': 'application/json'}, ...options});
  const result = await response.json();
  if (!response.ok) throw new Error(result.message || 'Something went wrong');
  return result;
}

async function refresh() {
  try {
    state.data = await api('/api/status');
    render();
  } catch (error) {
    toast('Server connection lost');
  }
}

function render() {
  const {slots, counts, activity} = state.data;
  $('#available-count').textContent = counts.available;
  $('#occupied-count').textContent = counts.occupied;
  $('#booked-count').textContent = counts.booked;
  $('#used-count').textContent = counts.occupied + counts.booked;
  const next = slots.find(slot => slot.status === 'available');
  $('#next-slot').textContent = next ? label(next) : 'FULL';
  $('#book-next').disabled = !next;
  $('#book-next').dataset.slot = next?.id || '';
  renderZone('#zone-a', slots.filter(slot => slot.zone === 'A'));
  renderZone('#zone-b', slots.filter(slot => slot.zone === 'B'));
  $('#activity-list').innerHTML = activity.slice(0, 7).map(item => `
    <article class="activity-item"><span class="dot">${activityIcon(item.title)}</span>
      <div><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.detail)}</p></div><time>${item.time}</time></article>`).join('');
}

function renderZone(selector, slots) {
  $(selector).innerHTML = slots.map(slot => `
    <button class="slot ${slot.status}" data-slot="${slot.id}" aria-label="${label(slot)} ${slot.status}">
      <span class="slot-id">${label(slot)}</span><span class="car">${slot.status === 'available' ? '⌄' : '▰'}</span>
      <span class="slot-status">${slot.status === 'booked' ? 'reserved' : slot.status}</span>
    </button>`).join('');
}

function label(slot) { return `${slot.zone}-${String(slot.id).padStart(2, '0')}`; }
function activityIcon(title) { return title.includes('book') ? '◆' : title.includes('exit') ? '↗' : title.includes('enter') ? '↘' : '✓'; }
function escapeHtml(value) { const div = document.createElement('div'); div.textContent = value; return div.innerHTML; }

function openBooking(slotId) {
  const slot = state.data.slots.find(item => item.id === Number(slotId));
  if (!slot) return;
  if (slot.status === 'booked') {
    if (confirm(`Cancel the reservation for ${label(slot)}?`)) cancelBooking(slot.id);
    return;
  }
  if (slot.status !== 'available') return;
  state.selectedSlot = slot.id;
  $('#dialog-slot').textContent = label(slot);
  $('#booking-dialog').showModal();
  $('#driver-name').focus();
}

async function cancelBooking(slotId) {
  try {
    const result = await api(`/api/slots/${slotId}/cancel`, {method: 'POST', body: '{}'});
    state.data = result.data; render(); toast(result.message);
  } catch (error) { toast(error.message); }
}

$('#spaces').addEventListener('click', event => {
  const slot = event.target.closest('.slot');
  if (slot) openBooking(slot.dataset.slot);
});
$('#book-next').addEventListener('click', event => openBooking(event.currentTarget.dataset.slot));
$('.dialog-close').addEventListener('click', () => $('#booking-dialog').close());
$('#booking-form').addEventListener('submit', async event => {
  event.preventDefault();
  const body = JSON.stringify({name: $('#driver-name').value, vehicle: $('#vehicle-number').value});
  try {
    const result = await api(`/api/slots/${state.selectedSlot}/book`, {method: 'POST', body});
    state.data = result.data; render(); $('#booking-dialog').close(); event.target.reset(); toast(result.message);
  } catch (error) { toast(error.message); }
});
$('#simulate').addEventListener('click', async () => {
  try { const result = await api('/api/simulate', {method: 'POST', body: '{}'}); state.data = result.data; render(); toast(result.message); }
  catch (error) { toast(error.message); }
});
function toast(message) { const el = $('#toast'); el.textContent = message; el.classList.add('show'); clearTimeout(window.toastTimer); window.toastTimer = setTimeout(() => el.classList.remove('show'), 2600); }

refresh();
setInterval(refresh, 5000);
