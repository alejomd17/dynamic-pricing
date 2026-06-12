"use client";

interface KPIFiltersBarProps {
  products: string[];
  selectedProduct: string;
  onProductChange: (product: string) => void;
  price: number;
  onPriceChange: (price: number) => void;
  cost: number;
  onCostChange: (cost: number) => void;
  transactions: number;
  customers: number;
}

export default function KPIFiltersBar({
  products,
  selectedProduct,
  onProductChange,
  price,
  onPriceChange,
  cost,
  onCostChange,
  transactions,
  customers,
}: KPIFiltersBarProps) {
  return (
    <div
      style={{ backgroundColor: "#00285d", borderRadius: "18px" }}
      className="p-6 mb-8"
    >
      <div className="grid grid-cols-2 md:grid-cols-5 gap-6 items-end">
        {/* Producto */}
        <div>
          <label
            className="block text-xs font-semibold uppercase tracking-widest mb-2"
            style={{ color: "#93c5fd" }}
          >
            Producto
          </label>
          <select
            value={selectedProduct}
            onChange={(e) => onProductChange(e.target.value)}
            className="w-full px-3 py-2 rounded-lg text-white text-sm font-medium focus:outline-none focus:ring-2"
            style={{
              backgroundColor: "rgba(255,255,255,0.12)",
              border: "1px solid rgba(255,255,255,0.25)",
              color: "white",
            }}
          >
            {products.map((p) => (
              <option key={p} value={p} style={{ backgroundColor: "#00285d" }}>
                {p}
              </option>
            ))}
          </select>
        </div>

        {/* Precio */}
        <div>
          <label
            className="block text-xs font-semibold uppercase tracking-widest mb-2"
            style={{ color: "#93c5fd" }}
          >
            Precio
          </label>
          <input
            type="number"
            value={price}
            onChange={(e) => onPriceChange(Number(e.target.value))}
            min={0}
            step={1}
            className="w-full px-3 py-2 rounded-lg text-white text-sm font-medium focus:outline-none focus:ring-2"
            style={{
              backgroundColor: "rgba(255,255,255,0.12)",
              border: "1px solid rgba(255,255,255,0.25)",
            }}
          />
        </div>

        {/* Costo */}
        <div>
          <label
            className="block text-xs font-semibold uppercase tracking-widest mb-2"
            style={{ color: "#93c5fd" }}
          >
            Costo
          </label>
          <input
            type="number"
            value={cost}
            onChange={(e) => onCostChange(Number(e.target.value))}
            min={0}
            step={1}
            className="w-full px-3 py-2 rounded-lg text-white text-sm font-medium focus:outline-none focus:ring-2"
            style={{
              backgroundColor: "rgba(255,255,255,0.12)",
              border: "1px solid rgba(255,255,255,0.25)",
            }}
          />
        </div>

        {/* Transacciones */}
        <div>
          <label
            className="block text-xs font-semibold uppercase tracking-widest mb-2"
            style={{ color: "#93c5fd" }}
          >
            Transacciones
          </label>
          <div className="text-2xl font-bold text-white">
            {transactions.toLocaleString()}
          </div>
        </div>

        {/* Num. Clientes */}
        <div>
          <label
            className="block text-xs font-semibold uppercase tracking-widest mb-2"
            style={{ color: "#93c5fd" }}
          >
            Num. Clientes
          </label>
          <div className="text-2xl font-bold text-white">
            {customers.toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );
}
