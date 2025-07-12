# Tushar SuperStore - Advanced Inventory Management System

A modern, real-time inventory management system built with Flask, featuring an interactive dashboard with live analytics and beautiful visualizations.

## 🚀 Features

### 📊 Real-Time Analytics Dashboard
- **Live KPI Monitoring**: Revenue, bills, products, and performance metrics
- **Interactive Charts**: Sales trends, category distribution, top products, inventory levels
- **Auto-Refresh**: Updates every 30 seconds with manual refresh option
- **Visual Notifications**: Success/error messages with smooth animations
- **Responsive Design**: Works perfectly on desktop and mobile devices

### 📦 Inventory Management
- **Product Management**: Add, edit, delete products with categories
- **Stock Tracking**: Real-time inventory levels with color-coded alerts
- **Low Stock Alerts**: Automatic warnings for products below threshold
- **Category Organization**: Organize products by categories

### 🧾 Billing System
- **Invoice Generation**: Professional PDF bill generation
- **Draft Bills**: Save incomplete bills for later completion
- **Stock Deduction**: Automatic inventory updates on sales
- **Bill History**: Track all completed transactions

### 🎨 Modern UI/UX
- **Beautiful Design**: Gradient cards, hover effects, and smooth transitions
- **Professional Layout**: Clean, intuitive interface
- **Visual Feedback**: Loading states and update animations
- **Mobile Responsive**: Optimized for all screen sizes

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Bootstrap 5, JavaScript ES6
- **Charts**: Plotly.js for interactive visualizations
- **PDF Generation**: ReportLab
- **Analytics**: Pandas for data processing

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/tushar-superstore.git
   cd tushar-superstore
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open in browser**
   Navigate to `http://127.0.0.1:5000`

## 📁 Project Structure

```
tushar-superstore/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── logo.png              # Store logo
├── instance/
│   └── store.db          # SQLite database
├── templates/
│   ├── index.html        # Main inventory page
│   ├── dashboard.html    # Analytics dashboard
│   ├── create_bill.html  # Billing interface
│   ├── add_product.html  # Add product form
│   ├── edit_product.html # Edit product form
│   └── add_category.html # Add category form
└── GeneratedBills/       # PDF bills storage
```

## 🎯 Key Features Explained

### Real-Time Dashboard
- **Automatic Updates**: Dashboard refreshes every 30 seconds
- **Manual Refresh**: Instant update with refresh button
- **Live Metrics**: Revenue, sales, inventory tracked in real-time
- **Visual Charts**: Interactive Plotly charts for data visualization

### Inventory Alerts
- 🔴 **Critical**: Less than 5 items in stock
- 🟡 **Warning**: Less than 20 items in stock  
- 🟢 **Good**: Adequate stock levels

### PDF Bill Generation
- Professional invoice layout with company logo
- Detailed itemization with quantities and prices
- Automatic file naming and storage
- Print-ready format

## 🔧 Configuration

### Database Setup
The application automatically creates the SQLite database on first run. No manual setup required.

### Adding Logo
Place your `logo.png` file in the root directory to display on bills and dashboard.

### Customization
- Modify `app.py` for business logic changes
- Update templates in `templates/` for UI changes
- Adjust styles in dashboard.html for visual customization

## 📊 Dashboard Metrics

### Key Performance Indicators
- **Total Revenue**: Sum of all completed sales
- **Total Bills**: Number of transactions
- **Average Bill Value**: Mean transaction amount
- **Today/Week/Month Sales**: Time-based analytics

### Charts Available
1. **Sales Trend**: Daily sales over time (Line Chart)
2. **Category Distribution**: Sales by product category (Pie Chart)
3. **Top Products**: Best-selling items by revenue (Bar Chart)
4. **Inventory Levels**: Current stock status (Bar Chart)

## 🚦 API Endpoints

- `/api/dashboard_metrics` - Get all dashboard data as JSON
- `/api/sales_chart` - Sales trend chart data
- `/api/category_chart` - Category distribution data
- `/api/top_products_chart` - Top products data
- `/api/inventory_chart` - Inventory levels data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Tushar**
- GitHub: [@tushaarmahajan](https://github.com/tushaarmahajan)

## 🙏 Acknowledgments

- Flask framework for the robust backend
- Bootstrap for the responsive UI components
- Plotly.js for beautiful interactive charts
- ReportLab for professional PDF generation

## 📞 Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

⭐ **Star this repository if you find it useful!** ⭐
