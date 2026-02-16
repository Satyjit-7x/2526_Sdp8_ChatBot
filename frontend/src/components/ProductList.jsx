import { useState, useEffect } from 'react';
import './ProductList.css';

const ProductList = () => {
    const [products, setProducts] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedCategory, setSelectedCategory] = useState('All');

    useEffect(() => {
        fetchProducts();
    }, []);

    const fetchProducts = async () => {
        try {
            const response = await fetch('http://localhost:5001/api/products');
            const data = await response.json();
            if (data.products) {
                setProducts(data.products);
            }
        } catch (error) {
            console.error('Error fetching products:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const categories = ['All', ...new Set(products.map(p => p.category))];
    const filteredProducts = selectedCategory === 'All'
        ? products
        : products.filter(p => p.category === selectedCategory);

    return (
        <div className="product-list">
            <h2>Available Products</h2>

            <div className="category-filter">
                {categories.map(cat => (
                    <button
                        key={cat}
                        className={selectedCategory === cat ? 'active' : ''}
                        onClick={() => setSelectedCategory(cat)}
                    >
                        {cat}
                    </button>
                ))}
            </div>

            {isLoading ? (
                <p>Loading products...</p>
            ) : (
                <div className="products">
                    {filteredProducts.map(product => (
                        <div key={product.productId} className="product-card">
                            <h3>{product.name}</h3>
                            {product.description && <p className="description">{product.description}</p>}
                            {product.price && (
                                <p className="price">
                                    ₹{product.price.toLocaleString('en-IN', {
                                        minimumFractionDigits: 0,
                                        maximumFractionDigits: 0
                                    })}
                                </p>
                            )}
                            <span className="category">{product.category}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ProductList;
