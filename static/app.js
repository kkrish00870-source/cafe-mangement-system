let state = { menu: [], orders: [] };
const cart = new Map();
const money = value => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(value / 100);
const el = id => document.getElementById(id);
const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
let messageTimer;
function message(text) { el('message').textContent = text; clearTimeout(messageTimer); messageTimer = setTimeout(() => el('message').textContent = '', 5000); }
async function request(path, data) {
  const response = await fetch(path, data === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed');
  return result;
}
function renderCart() {
  let total = 0;
  el('cart').innerHTML = [...cart].map(([id, quantity]) => {
    const item = state.menu.find(item => item.id === id); total += item.price * quantity;
    return `<div class="cart-row"><span>${escapeHTML(item.name)} × ${quantity}</span><span>${money(item.price * quantity)} <button type="button" data-remove="${id}" aria-label="Remove one ${escapeHTML(item.name)}">−</button></span></div>`;
  }).join('') || '<p class="subtle">Choose a little something from the menu.</p>';
  el('total').textContent = money(total);
}
function render() {
  const icons = ['☕', '☕', '🧊', '🍵', '🥐', '🍫'];
  el('menu').innerHTML = state.menu.map((item, index) => `<button type="button" class="product" data-add="${item.id}"><span aria-hidden="true">${icons[index % icons.length]}</span><b>${escapeHTML(item.name)}</b><small>${money(item.price)} <span style="float:right;font-size:16px">+</span></small></button>`).join('');
  const completed = state.orders.filter(order => order.status === 'Completed');
  el('revenue').textContent = money(completed.reduce((total, order) => total + order.total, 0));
  el('completed').textContent = completed.length;
  el('active').textContent = state.orders.filter(order => ['Preparing', 'Ready'].includes(order.status)).length;
  const transitions = { Preparing: ['Ready', 'Cancelled'], Ready: ['Completed', 'Cancelled'], Completed: [], Cancelled: [] };
  el('orders').innerHTML = state.orders.map(order => `<article class="order"><div class="order-head"><b>#${order.id} · ${escapeHTML(order.customer)}</b><strong>${money(order.total)}</strong></div><p>${order.items.map(item => `${item.quantity} × ${escapeHTML(item.name)}`).join(' · ')}<br>${new Date(order.created_at.replace(' ', 'T') + 'Z').toLocaleString()}</p><select data-status="${order.id}" aria-label="Order ${order.id} status" ${transitions[order.status].length ? '' : 'disabled'}>${[order.status, ...transitions[order.status]].map(status => `<option>${status}</option>`).join('')}</select></article>`).join('') || '<div class="empty">Your next great order starts with the menu. ☕</div>';
  renderCart();
}
async function refresh() { state = await request('/api/state'); render(); }
el('menu').addEventListener('click', event => { const button = event.target.closest('[data-add]'); if (button) { const id = Number(button.dataset.add); cart.set(id, Math.min(99, (cart.get(id) || 0) + 1)); renderCart(); } });
el('cart').addEventListener('click', event => { const button = event.target.closest('[data-remove]'); if (button) { const id = Number(button.dataset.remove); if (cart.get(id) > 1) cart.set(id, cart.get(id) - 1); else cart.delete(id); renderCart(); } });
el('order-form').addEventListener('submit', async event => {
  event.preventDefault(); if (!cart.size) return message('Choose at least one menu item.');
  el('submit').disabled = true;
  try { await request('/api/orders', { customer: el('customer').value, items: [...cart].map(([id, quantity]) => ({ id, quantity })) }); cart.clear(); el('customer').value = ''; renderCart(); message('Order placed. Let’s get brewing!'); await refresh(); }
  catch (error) { message(error.message); } finally { el('submit').disabled = false; }
});
el('orders').addEventListener('change', async event => { if (!event.target.matches('[data-status]')) return; event.target.disabled = true; try { await request(`/api/orders/${event.target.dataset.status}/status`, { status: event.target.value }); await refresh(); } catch (error) { message(error.message); await refresh().catch(() => {}); } });
el('refresh').addEventListener('click', () => refresh().catch(error => message(error.message)));
el('date').textContent = new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' });
refresh().catch(error => message(error.message));
