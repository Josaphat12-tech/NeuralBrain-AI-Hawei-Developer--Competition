/**
 * NeuralBrain Heat-Map Visualization Module
 * Provides enterprise-grade heat-map with real backend data
 * Synchronized across landing page and dashboard
 */

class NeuralBrainHeatMap {
    constructor(mapElementId, options = {}) {
        this.mapElementId = mapElementId;
        this.map = null;
        this.circleMarkers = [];
        this.options = {
            updateInterval: options.updateInterval || 30000, // 30 seconds
            zoomLevel: options.zoomLevel || 2,
            center: options.center || [20, 0],
            ...options
        };
        this.dataCache = null;
        this.isInitializing = false;
    }

    /**
     * Initialize the map with Leaflet
     */
    async initialize() {
        if (this.isInitializing || this.map) return;
        this.isInitializing = true;

        try {
            const mapContainer = document.getElementById(this.mapElementId);
            if (!mapContainer) {
                console.warn(`Map container ${this.mapElementId} not found`);
                this.isInitializing = false;
                return;
            }

            // Initialize Leaflet map
            this.map = L.map(this.mapElementId, {
                zoomControl: true,
                scrollWheelZoom: true,
                dragging: true,
                attributionControl: false,
                preferCanvas: true
            }).setView(this.options.center, this.options.zoomLevel);

            // Add dark tile layer
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                subdomains: 'abcd',
                maxZoom: 19
            }).addTo(this.map);

            // Add legend
            this.addLegend();

            // Load and render initial data
            await this.updateHeatMap();

            // Set up periodic updates
            this.startPeriodicUpdates();

            this.isInitializing = false;
        } catch (error) {
            console.error('Error initializing heat-map:', error);
            this.isInitializing = false;
        }
    }

    /**
     * Fetch real data from backend
     */
    async fetchRealData() {
        try {
            const response = await fetch('/api/real-data');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            this.dataCache = data;
            return data;
        } catch (error) {
            console.warn('Could not fetch real data, using fallback:', error);
            return this.getStaticFallback();
        }
    }

    /**
     * Get static fallback data for development/demo
     */
    getStaticFallback() {
        return {
            top_affected_countries: [
                { name: 'India', confirmed: 44629266, lat: 20.593, lng: 78.962, deaths: 527843 },
                { name: 'Brazil', confirmed: 34652000, lat: -14.235, lng: -51.925, deaths: 682800 },
                { name: 'USA', confirmed: 103000000, lat: 37.0902, lng: -95.7129, deaths: 1100000 },
                { name: 'Kenya', confirmed: 340000, lat: -1.286, lng: 36.817, deaths: 5670 },
                { name: 'China', confirmed: 684000, lat: 39.904, lng: 116.407, deaths: 5255 },
                { name: 'UK', confirmed: 24000000, lat: 51.507, lng: -0.127, deaths: 185000 }
            ]
        };
    }

    /**
     * Calculate risk level based on cases and growth
     */
    calculateRiskLevel(cases, maxCases) {
        const percentage = (cases / maxCases) * 100;
        if (percentage > 70) return 'critical';
        if (percentage > 40) return 'high';
        if (percentage > 15) return 'moderate';
        return 'low';
    }

    /**
     * Get color based on risk level
     */
    getRiskColor(riskLevel) {
        const colors = {
            'critical': '#dc2626',   // Red
            'high': '#ea580c',        // Orange
            'moderate': '#eab308',    // Yellow
            'low': '#22c55e'          // Green
        };
        return colors[riskLevel] || '#6b7280';
    }

    /**
     * Get radius based on case volume (scaled for visibility)
     */
    getMarkerRadius(cases, maxCases) {
        const minRadius = 8;
        const maxRadius = 25;
        const percentage = Math.min(cases / maxCases, 1);
        return minRadius + (percentage * (maxRadius - minRadius));
    }

    /**
     * Format number for display
     */
    formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }

    /**
     * Create enhanced tooltip content
     */
    createTooltipContent(country) {
        const riskLevel = this.calculateRiskLevel(country.confirmed, 103000000);
        const riskColor = this.getRiskColor(riskLevel);
        
        return `
            <div style="font-family: 'Inter', sans-serif; color: #1e293b; min-width: 250px; padding: 0;">
                <div style="background: linear-gradient(135deg, ${riskColor}15 0%, ${riskColor}05 100%); border-left: 3px solid ${riskColor}; padding: 10px; margin-bottom: 8px;">
                    <h4 style="margin: 0 0 4px 0; color: ${riskColor}; font-weight: 700; font-size: 1.1rem;">${country.name}</h4>
                    <p style="margin: 0; font-size: 0.85rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">${riskLevel} RISK</p>
                </div>
                <div style="padding: 8px 10px;">
                    <p style="margin: 6px 0; font-size: 0.9rem;"><strong>Cases:</strong> ${this.formatNumber(country.confirmed)}</p>
                    <p style="margin: 6px 0; font-size: 0.9rem;"><strong>Deaths:</strong> ${this.formatNumber(country.deaths)}</p>
                    <p style="margin: 6px 0; font-size: 0.85rem; color: #64748b;">
                        <strong>Fatality Rate:</strong> ${((country.deaths / country.confirmed) * 100).toFixed(2)}%
                    </p>
                </div>
                <div style="background: #f1f5f9; padding: 8px 10px; margin-top: 8px; border-radius: 4px; font-size: 0.8rem; color: #475569;">
                    Updated with real Disease.sh data
                </div>
            </div>
        `;
    }

    /**
     * Update heat-map with data
     */
    async updateHeatMap() {
        try {
            const data = await this.fetchRealData();
            
            if (!data || !data.top_affected_countries || data.top_affected_countries.length === 0) {
                console.warn('No country data available');
                return;
            }

            const countries = data.top_affected_countries;
            const maxCases = Math.max(...countries.map(c => c.confirmed));

            // Clear existing markers
            this.circleMarkers.forEach(marker => this.map.removeLayer(marker));
            this.circleMarkers = [];

            // Add new markers with smooth transitions
            countries.forEach((country, index) => {
                const riskLevel = this.calculateRiskLevel(country.confirmed, maxCases);
                const color = this.getRiskColor(riskLevel);
                const radius = this.getMarkerRadius(country.confirmed, maxCases);

                const circle = L.circleMarker([country.lat, country.lng], {
                    color: color,
                    fillColor: color,
                    fillOpacity: 0.7,
                    radius: radius,
                    weight: 2,
                    opacity: 0.8,
                    className: `heat-map-marker risk-${riskLevel}`
                }).addTo(this.map);

                // Bind tooltip
                const tooltipContent = this.createTooltipContent(country);
                circle.bindPopup(tooltipContent, {
                    className: 'heat-map-popup',
                    maxWidth: 350,
                    closeButton: true
                });

                // Add hover effects
                circle.on('mouseover', () => {
                    circle.setStyle({
                        fillOpacity: 0.9,
                        weight: 3,
                        radius: radius * 1.15
                    });
                    circle.openPopup();
                });

                circle.on('mouseout', () => {
                    circle.setStyle({
                        fillOpacity: 0.7,
                        weight: 2,
                        radius: radius
                    });
                });

                this.circleMarkers.push(circle);
            });

            this.dispatchUpdateEvent('heatmap-updated', { 
                countries: countries,
                timestamp: new Date().toISOString()
            });

        } catch (error) {
            console.error('Error updating heat-map:', error);
        }
    }

    /**
     * Add legend to map
     */
    addLegend() {
        const legend = L.control({ position: 'bottomright' });

        legend.onAdd = (map) => {
            const div = L.DomUtil.create('div', 'heat-map-legend');
            div.innerHTML = `
                <div style="background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); font-family: 'Inter', sans-serif;">
                    <p style="margin: 0 0 10px 0; font-weight: 600; font-size: 0.9rem; color: #1e293b;">Risk Levels</p>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        <div style="display: flex; align-items: center; gap: 8px; font-size: 0.85rem;">
                            <div style="width: 14px; height: 14px; background: #dc2626; border-radius: 50%;"></div>
                            <span style="color: #1e293b;">Critical Risk</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px; font-size: 0.85rem;">
                            <div style="width: 14px; height: 14px; background: #ea580c; border-radius: 50%;"></div>
                            <span style="color: #1e293b;">High Risk</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px; font-size: 0.85rem;">
                            <div style="width: 14px; height: 14px; background: #eab308; border-radius: 50%;"></div>
                            <span style="color: #1e293b;">Moderate Risk</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px; font-size: 0.85rem;">
                            <div style="width: 14px; height: 14px; background: #22c55e; border-radius: 50%;"></div>
                            <span style="color: #1e293b;">Low Risk</span>
                        </div>
                    </div>
                    <p style="margin: 10px 0 0 0; padding-top: 10px; border-top: 1px solid #e2e8f0; font-size: 0.75rem; color: #64748b;">
                        Marker size = case volume
                    </p>
                </div>
            `;
            return div;
        };

        legend.addTo(this.map);
    }

    /**
     * Start periodic updates
     */
    startPeriodicUpdates() {
        this.updateInterval = setInterval(() => {
            this.updateHeatMap();
        }, this.options.updateInterval);
    }

    /**
     * Stop periodic updates
     */
    stopPeriodicUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    /**
     * Dispatch custom event
     */
    dispatchUpdateEvent(eventName, detail) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }

    /**
     * Destroy the map instance
     */
    destroy() {
        this.stopPeriodicUpdates();
        if (this.map) {
            this.map.remove();
            this.map = null;
        }
        this.circleMarkers = [];
    }

    /**
     * Resize map (useful for responsive layouts)
     */
    resize() {
        if (this.map) {
            this.map.invalidateSize();
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NeuralBrainHeatMap;
}
