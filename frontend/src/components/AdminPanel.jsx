import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import './AdminPanel.css';

const API_BASE = 'http://localhost:5001/api';

const AdminPanel = ({ onSwitchToChat }) => {
    const { user, logout } = useAuth();
    const [stats, setStats] = useState(null);
    const [orders, setOrders] = useState([]);
    const [users, setUsers] = useState([]);
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [updatingId, setUpdatingId] = useState(null);
    const [activeView, setActiveView] = useState('orders');
    const [showCreateProduct, setShowCreateProduct] = useState(false);
    const [newProduct, setNewProduct] = useState({ name: '', description: '', price: '', category: '', inStock: true });
    const [createError, setCreateError] = useState('');
    const [creatingProduct, setCreatingProduct] = useState(false);
    const [togglingStockId, setTogglingStockId] = useState(null);

    const fetchStats = async () => {
        try {
            const res = await fetch(`${API_BASE}/admin/stats`);
            const data = await res.json();
            setStats(data);
        } catch (err) {
            console.error('Stats error:', err);
        }
    };

    const fetchOrders = async () => {
        try {
            const res = await fetch(`${API_BASE}/orders`);
            const data = await res.json();
            setOrders(data.orders || []);
        } catch (err) {
            console.error('Orders error:', err);
        } finally {
            setLoading(false);
        }
    };

    const fetchUsers = async () => {
        try {
            const res = await fetch(`${API_BASE}/admin/users`);
            const data = await res.json();
            setUsers(data.users || []);
        } catch (err) {
            console.error('Users error:', err);
        }
    };

    const fetchProducts = async () => {
        try {
            const res = await fetch(`${API_BASE}/products?all=1`);
            const data = await res.json();
            setProducts(data.products || []);
        } catch (err) {
            console.error('Products error:', err);
        }
    };

    useEffect(() => {
        fetchStats();
        fetchOrders();
        fetchUsers();
        fetchProducts();
    }, []);

    const handleStatusUpdate = async (orderId, newStatus) => {
        setUpdatingId(orderId);
        try {
            const res = await fetch(`${API_BASE}/orders/${orderId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus }),
            });
            if (res.ok) {
                setOrders(prev =>
                    prev.map(o => o.orderId === orderId ? { ...o, status: newStatus } : o)
                );
                fetchStats();
            }
        } catch (err) {
            console.error('Update error:', err);
        } finally {
            setUpdatingId(null);
        }
    };

    const handleDelete = async (orderId) => {
        if (!window.confirm(`Delete order ${orderId}?`)) return;
        try {
            const res = await fetch(`${API_BASE}/orders/${orderId}`, { method: 'DELETE' });
            if (res.ok) {
                setOrders(prev => prev.filter(o => o.orderId !== orderId));
                fetchStats();
            }
        } catch (err) {
            console.error('Delete error:', err);
        }
    };

    const handleToggleStock = async (productId, currentInStock) => {
        setTogglingStockId(productId);
        try {
            const res = await fetch(`${API_BASE}/products/${productId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ inStock: !currentInStock }),
            });
            if (res.ok) {
                setProducts(prev =>
                    prev.map(p => p.productId === productId ? { ...p, inStock: !currentInStock } : p)
                );
                fetchStats();
            }
        } catch (err) {
            console.error('Toggle stock error:', err);
        } finally {
            setTogglingStockId(null);
        }
    };

    const handleCreateProduct = async (e) => {
        e.preventDefault();
        setCreateError('');
        if (!newProduct.name.trim() || !newProduct.price || !newProduct.category.trim()) {
            setCreateError('Name, price, and category are required.');
            return;
        }
        if (isNaN(newProduct.price) || Number(newProduct.price) <= 0) {
            setCreateError('Price must be a valid positive number.');
            return;
        }
        setCreatingProduct(true);
        try {
            const res = await fetch(`${API_BASE}/products`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: newProduct.name.trim(),
                    description: newProduct.description.trim(),
                    price: Number(newProduct.price),
                    category: newProduct.category.trim(),
                    inStock: newProduct.inStock,
                }),
            });
            const data = await res.json();
            if (res.ok && data.success) {
                setProducts(prev => [...prev, data.product]);
                setNewProduct({ name: '', description: '', price: '', category: '', inStock: true });
                setShowCreateProduct(false);
                fetchStats();
            } else {
                setCreateError(data.error || 'Failed to create product.');
            }
        } catch (err) {
            console.error('Create product error:', err);
            setCreateError('Server error. Please try again.');
        } finally {
            setCreatingProduct(false);
        }
    };

    const filteredOrders = orders.filter(o => {
        const matchesSearch = !searchTerm ||
            o.orderId?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            o.productName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            o.creatorName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            o.creatorEmail?.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = statusFilter === 'all' || o.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    const filteredUsers = users.filter(u => {
        if (!searchTerm) return true;
        const term = searchTerm.toLowerCase();
        return u.name?.toLowerCase().includes(term) || u.email?.toLowerCase().includes(term);
    });

    const filteredProducts = products.filter(p => {
        if (!searchTerm) return true;
        const term = searchTerm.toLowerCase();
        return p.name?.toLowerCase().includes(term) || p.category?.toLowerCase().includes(term) || p.description?.toLowerCase().includes(term);
    });

    const handleStatClick = (view) => {
        setActiveView(view);
        setSearchTerm('');
        setStatusFilter('all');
    };

    const existingCategories = [...new Set(products.map(p => p.category).filter(Boolean))];
    const statuses = ['Pending', 'Shipped', 'Delivered', 'Cancelled', 'Returned'];

    return (
        <div className="admin-container">
            {/* Header */}
            <header className="admin-header">
                <div className="admin-header-left">
                    <h1>⚙️ Admin Dashboard</h1>
                    <span className="admin-badge">ADMIN</span>
                </div>
                <div className="admin-header-right">
                    <button className="admin-btn-chat" onClick={onSwitchToChat}>💬 Chat View</button>
                    <div className="user-info">
                        <span className="user-name">{user?.name || 'Admin'}</span>
                        <button className="logout-btn" onClick={logout}>Logout</button>
                    </div>
                </div>
            </header>

            {/* Stats Cards */}
            {stats && (
                <div className="stats-grid">
                    <div className={`stat-card stat-orders clickable ${activeView === 'orders' ? 'stat-active' : ''}`} onClick={() => handleStatClick('orders')}>
                        <div className="stat-icon">📦</div>
                        <div className="stat-info">
                            <span className="stat-value">{stats.totalOrders}</span>
                            <span className="stat-label">Total Orders</span>
                        </div>
                    </div>
                    <div className={`stat-card stat-products clickable ${activeView === 'products' ? 'stat-active' : ''}`} onClick={() => handleStatClick('products')}>
                        <div className="stat-icon">🛍️</div>
                        <div className="stat-info">
                            <span className="stat-value">{stats.totalProducts}</span>
                            <span className="stat-label">Products</span>
                        </div>
                    </div>
                    <div className={`stat-card stat-users clickable ${activeView === 'users' ? 'stat-active' : ''}`} onClick={() => handleStatClick('users')}>
                        <div className="stat-icon">👥</div>
                        <div className="stat-info">
                            <span className="stat-value">{stats.totalUsers}</span>
                            <span className="stat-label">Users</span>
                        </div>
                    </div>
                    <div className={`stat-card stat-revenue clickable ${activeView === 'orders' ? 'stat-active' : ''}`} onClick={() => handleStatClick('orders')}>
                        <div className="stat-icon">💰</div>
                        <div className="stat-info">
                            <span className="stat-value">₹{stats.totalRevenue?.toLocaleString('en-IN')}</span>
                            <span className="stat-label">Revenue</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Status Summary — only for orders view */}
            {activeView === 'orders' && stats?.statusCounts && (
                <div className="status-summary">
                    {Object.entries(stats.statusCounts).map(([status, count]) => (
                        <button
                            key={status}
                            className={`status-chip status-chip-${status.toLowerCase()} ${statusFilter === status ? 'active' : ''}`}
                            onClick={() => setStatusFilter(statusFilter === status ? 'all' : status)}
                        >
                            {status}: {count}
                        </button>
                    ))}
                    {statusFilter !== 'all' && (
                        <button className="status-chip status-chip-clear" onClick={() => setStatusFilter('all')}>
                            ✕ Clear
                        </button>
                    )}
                </div>
            )}

            {/* Search & Filter */}
            <div className="admin-toolbar">
                <input
                    type="text"
                    className="admin-search"
                    placeholder={
                        activeView === 'orders' ? 'Search by Order ID, Product, or User...' :
                        activeView === 'users' ? 'Search by name or email...' :
                        'Search by product name or category...'
                    }
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
                <span className="admin-count">
                    {activeView === 'orders' && `${filteredOrders.length} order${filteredOrders.length !== 1 ? 's' : ''}`}
                    {activeView === 'users' && `${filteredUsers.length} user${filteredUsers.length !== 1 ? 's' : ''}`}
                    {activeView === 'products' && `${filteredProducts.length} product${filteredProducts.length !== 1 ? 's' : ''}`}
                </span>
                {activeView === 'products' && (
                    <button className="add-product-btn" onClick={() => setShowCreateProduct(!showCreateProduct)}>
                        {showCreateProduct ? '✕ Cancel' : '＋ Add Product'}
                    </button>
                )}
            </div>

            {/* Create Product Form */}
            {showCreateProduct && (
                <div className="create-product-panel">
                    <form className="create-product-form" onSubmit={handleCreateProduct}>
                        <h3>Create New Product</h3>
                        {createError && <div className="create-error">{createError}</div>}
                        <div className="form-row">
                            <div className="form-field">
                                <label>Product Name *</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Wireless Mouse"
                                    value={newProduct.name}
                                    onChange={(e) => setNewProduct(prev => ({ ...prev, name: e.target.value }))}
                                    disabled={creatingProduct}
                                />
                            </div>
                            <div className="form-field">
                                <label>Category *</label>
                                <input
                                    type="text"
                                    placeholder="e.g. Electronics"
                                    list="category-list"
                                    value={newProduct.category}
                                    onChange={(e) => setNewProduct(prev => ({ ...prev, category: e.target.value }))}
                                    disabled={creatingProduct}
                                />
                                <datalist id="category-list">
                                    {existingCategories.map(c => <option key={c} value={c} />)}
                                </datalist>
                            </div>
                            <div className="form-field">
                                <label>Price (₹) *</label>
                                <input
                                    type="number"
                                    placeholder="999"
                                    min="1"
                                    step="any"
                                    value={newProduct.price}
                                    onChange={(e) => setNewProduct(prev => ({ ...prev, price: e.target.value }))}
                                    disabled={creatingProduct}
                                />
                            </div>
                        </div>
                        <div className="form-row">
                            <div className="form-field form-field-wide">
                                <label>Description</label>
                                <input
                                    type="text"
                                    placeholder="Brief product description..."
                                    value={newProduct.description}
                                    onChange={(e) => setNewProduct(prev => ({ ...prev, description: e.target.value }))}
                                    disabled={creatingProduct}
                                />
                            </div>
                            <div className="form-field form-field-checkbox">
                                <label>
                                    <input
                                        type="checkbox"
                                        checked={newProduct.inStock}
                                        onChange={(e) => setNewProduct(prev => ({ ...prev, inStock: e.target.checked }))}
                                        disabled={creatingProduct}
                                    />
                                    In Stock
                                </label>
                            </div>
                        </div>
                        <button type="submit" className="create-product-submit" disabled={creatingProduct}>
                            {creatingProduct ? '⏳ Creating...' : '✓ Create Product'}
                        </button>
                    </form>
                </div>
            )}

            {/* Content Area */}
            <div className="admin-table-wrapper">
                {/* ── ORDERS VIEW ── */}
                {activeView === 'orders' && (
                    <>
                        {loading ? (
                            <p className="admin-loading">Loading orders...</p>
                        ) : filteredOrders.length === 0 ? (
                            <p className="admin-empty">No orders found.</p>
                        ) : (
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>Order ID</th>
                                        <th>Product</th>
                                        <th>Ordered By</th>
                                        <th>Price</th>
                                        <th>Date</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredOrders.map((order) => (
                                        <tr key={order.orderId}>
                                            <td className="td-id">{order.orderId}</td>
                                            <td className="td-product">{order.productName}</td>
                                            <td className="td-user">
                                                <div className="user-cell">
                                                    <span className="user-cell-name">{order.creatorName || 'Unknown'}</span>
                                                    {order.creatorEmail && (
                                                        <span className="user-cell-email">{order.creatorEmail}</span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="td-price">₹{order.price?.toLocaleString('en-IN') || '0'}</td>
                                            <td className="td-date">{order.orderDate}</td>
                                            <td>
                                                <select
                                                    className={`status-select status-${(order.status || '').toLowerCase()}`}
                                                    value={order.status}
                                                    onChange={(e) => handleStatusUpdate(order.orderId, e.target.value)}
                                                    disabled={updatingId === order.orderId}
                                                >
                                                    {statuses.map(s => (
                                                        <option key={s} value={s}>{s}</option>
                                                    ))}
                                                </select>
                                            </td>
                                            <td>
                                                <button
                                                    className="delete-btn"
                                                    onClick={() => handleDelete(order.orderId)}
                                                    title="Delete order"
                                                >
                                                    🗑️
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </>
                )}

                {/* ── USERS VIEW ── */}
                {activeView === 'users' && (
                    <>
                        {filteredUsers.length === 0 ? (
                            <p className="admin-empty">No users found.</p>
                        ) : (
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>Name</th>
                                        <th>Email</th>
                                        <th>Role</th>
                                        <th>Orders</th>
                                        <th>Joined</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredUsers.map((u, idx) => (
                                        <tr key={u.userId}>
                                            <td className="td-id">{idx + 1}</td>
                                            <td className="td-product">
                                                <div className="user-cell">
                                                    <span className="user-cell-name">{u.name || 'N/A'}</span>
                                                </div>
                                            </td>
                                            <td className="td-email">{u.email}</td>
                                            <td>
                                                <span className={`role-badge role-${u.role || 'user'}`}>
                                                    {u.role || 'user'}
                                                </span>
                                            </td>
                                            <td className="td-center">{u.orderCount || 0}</td>
                                            <td className="td-date">{u.createdAt?.split('T')[0] || u.createdAt || '—'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </>
                )}

                {/* ── PRODUCTS VIEW ── */}
                {activeView === 'products' && (
                    <>
                        {filteredProducts.length === 0 ? (
                            <p className="admin-empty">No products found.</p>
                        ) : (
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Name</th>
                                        <th>Description</th>
                                        <th>Category</th>
                                        <th>Price</th>
                                        <th>In Stock</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredProducts.map((p) => (
                                        <tr key={p.productId} className={!p.inStock ? 'row-out-of-stock' : ''}>
                                            <td className="td-id">{p.productId}</td>
                                            <td className="td-product">{p.name}</td>
                                            <td className="td-desc">{p.description}</td>
                                            <td>
                                                <span className="category-badge">{p.category}</span>
                                            </td>
                                            <td className="td-price">₹{p.price?.toLocaleString('en-IN') || '0'}</td>
                                            <td className="td-center">
                                                <button
                                                    className={`stock-toggle-btn ${p.inStock ? 'in-stock' : 'out-stock'}`}
                                                    onClick={() => handleToggleStock(p.productId, p.inStock)}
                                                    disabled={togglingStockId === p.productId}
                                                    title={p.inStock ? 'Click to mark Out of Stock' : 'Click to mark In Stock'}
                                                >
                                                    {togglingStockId === p.productId ? '⏳' : p.inStock ? '✓ In Stock' : '✗ Out of Stock'}
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export default AdminPanel;
