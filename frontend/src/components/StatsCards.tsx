interface StatsCardsProps {
  stats: {
    rows: number;
    products: number;
    customers: number;
    date_range: {
      start: string;
      end: string;
    };
  };
}

export default function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    {
      title: "Transacciones",
      value: stats.rows.toLocaleString(),
      icon: "📊",
      color: "bg-blue-500",
    },
    {
      title: "Productos",
      value: stats.products.toLocaleString(),
      icon: "🏷️",
      color: "bg-green-500",
    },
    {
      title: "Clientes",
      value: stats.customers.toLocaleString(),
      icon: "👥",
      color: "bg-purple-500",
    },
    {
      title: "Periodo",
      value: `${stats.date_range.start.slice(0, 10)} → ${stats.date_range.end.slice(0, 10)}`,
      icon: "📅",
      color: "bg-orange-500",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {cards.map((card, index) => (
        <div
          key={index}
          className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow duration-200"
        >
          <div className="flex items-center justify-between mb-4">
            <span className="text-3xl">{card.icon}</span>
            <div className={`${card.color} w-2 h-12 rounded-full`}></div>
          </div>
          <h3 className="text-gray-600 text-sm font-medium mb-1">
            {card.title}
          </h3>
          <p className="text-2xl font-bold text-gray-900">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
