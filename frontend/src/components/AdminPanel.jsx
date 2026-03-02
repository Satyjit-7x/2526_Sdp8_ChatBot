import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import './AdminPanel.css';

const API_BASE = 'http://localhost:5001/api';

const AdminPanel = ({ onSwitchToChat }) => {
    const { user, logout } = useAuth();
    const [stats, setStats] = useState(null);
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [updatingId, setUpdatingId] = useState(null);

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

    useEffect(() => {
        fetchStats();
        fetchOrders();
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

    const filteredOrders = orders.filter(o => {
        const matchesSearch = !searchTerm ||
            o.orderId?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            o.productName?.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = statusFilter === 'all' || o.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

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
                    <div className="stat-card stat-orders">
                        <div className="stat-icon">📦</div>
                        <div className="stat-info">
                            <span className="stat-value">{stats.totalOrders}</span>
                            <span className="stat-label">Total Orders</span>
                        </div>
                    </div>
                    <div className="stat-card stat-products">
                        <div className="stat-icon">🛍️</div>
                        <div className="stat-info">
                            <span className="stat-value">{stats.totalProducts}</span>
                            <span className="stat-label">Products</span>
                        </div>
                    </div>
                    <div className="stat-card stat-users">
                        <div className="stat-icon">👥</div>
                        <div className="stat-info">
                            <span className="stat-value">{stats.totalUsers}</span>
                            <span className="stat-label">Users</span>
                        </div>
                    </div>
                    <div className="stat-card stat-revenue">
                        <div className="stat-icon">💰</div>
                        <div className="stat-info">
                            <span className="stat-value">₹{stats.totalRevenue?.toLocaleString('en-IN')}</span>
                            <span className="stat-label">Revenue</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Status Summary */}
            {stats?.statusCounts && (
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
                    placeholder="Search by Order ID or Product Name..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
                <span className="admin-count">{filteredOrders.length} order{filteredOrders.length !== 1 ? 's' : ''}</span>
            </div>

            {/* Orders Table */}
            <div className="admin-table-wrapper">
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
            </div>
        </div>
    );
};

export default AdminPanel;
