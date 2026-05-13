(function () {
    document.addEventListener("DOMContentLoaded", function () {
        var trendData = document.getElementById("trend-data");
        var canvas = document.getElementById("trendChart");

        if (!trendData || !canvas) return;

        try {
            var data = JSON.parse(trendData.textContent);
            if (!data || data.length === 0) return;

            var labels = data.map(function (d) { return d.date; });
            var scores = data.map(function (d) { return d.score; });

            var ctx = canvas.getContext("2d");
            var gradient = ctx.createLinearGradient(0, 0, 0, 250);
            gradient.addColorStop(0, "rgba(59, 130, 246, 0.2)");
            gradient.addColorStop(1, "rgba(59, 130, 246, 0.0)");

            new Chart(ctx, {
                type: "line",
                data: {
                    labels: labels,
                    datasets: [{
                        label: "Hygiene Score",
                        data: scores,
                        borderColor: "#3b82f6",
                        backgroundColor: gradient,
                        borderWidth: 2,
                        pointBackgroundColor: "#3b82f6",
                        pointBorderColor: "#ffffff",
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        fill: true,
                        tension: 0.3,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: "index",
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: "#0f172a",
                            titleColor: "#e2e8f0",
                            bodyColor: "#e2e8f0",
                            cornerRadius: 6,
                            padding: 10,
                        },
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: {
                                color: "#94a3b8",
                                font: { size: 11 },
                                maxRotation: 45,
                            },
                        },
                        y: {
                            min: 0,
                            max: 100,
                            grid: { color: "#f1f5f9" },
                            ticks: {
                                color: "#94a3b8",
                                font: { size: 11 },
                                callback: function (v) { return v.toFixed(0); },
                            },
                        },
                    },
                },
            });
        } catch (e) {
            console.warn("Failed to render trend chart:", e);
        }
    });

    document.body.addEventListener("htmx:afterSwap", function () {
        var trendData = document.getElementById("trend-data");
        var canvas = document.getElementById("trendChart");
        if (!trendData || !canvas) return;
        var existing = Chart.getChart(canvas);
        if (existing) existing.destroy();
        canvas.dispatchEvent(new Event("DOMContentLoaded"));
    });

    document.body.addEventListener("htmx:beforeSwap", function (evt) {
        var target = evt.detail.target;
        if (target) {
            target.style.opacity = "0";
            target.style.transition = "opacity 0.15s ease";
        }
    });

    document.body.addEventListener("htmx:afterSwap", function (evt) {
        var target = evt.detail.target;
        if (target) {
            target.style.opacity = "1";
            target.classList.add("fade-in");
        }
    });
})();
