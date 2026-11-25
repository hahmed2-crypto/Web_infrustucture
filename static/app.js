document.addEventListener("DOMContentLoaded", () =>{
    const presetCity= document.getElementById("preset-city");
    const cityInput= document.getElementById("city-input");
    const typeSelect= document.getElementById("type-select");
    const searchBtn= document.getElementById("search-btn");
    const filterInput= document.getElementById("filter-input");
    const sortSelect= document.getElementById("sort-select");
    const facilitiesGrid= document.getElementById("facilities-grid");
    const statusBar= document.getElementById("status-bar");
    const errorBox= document.getElementById("error-box");
    const serverNameEl= document.getElementById("server-name");
    const healthStatsGrid= document.getElementById("health-stats-grid");
    

    let currentFacilities= [];
    let resolvedLocation= "";

    function escapeHTML(text){
        const div= document.createElement("div");
        div.textContent= text ?? "";
        return div.innerHTML;
    }


    function showError(msg){
        errorBox.textContent = msg;
        errorBox.classList.remove("hidden");
        facilitiesGrid.innerHTML= "";
        statusBar.textContent= "";
    }

    function hideError(){
        errorBox.classList.add("hidden");
        errorBox.textContent= "";
    }


    // Loading the WOrld bank health Stats.

    async function loadHealthStats(){
        try{
            const res= await fetch("/api/health-stats");
            const data= await res.json();
            if (!res.ok || !data.stats) throw new Error();

            healthStatsGrid.innerHTML= data.stats.map(stat =>`
                <div class="stat-card">
                    <div class="stat-value">${escapeHTML(String(stat.value))}</div>
                    <div class="stat-label">${escapeHTML(stat.indicator)}</div>
                    <div class="stat-year">Latest data: ${escapeHTML(stat.year)}</div>
                </div>

            `).join("");
        } catch{
            healthStatsGrid.innerHTML= `<div class="stat-card"> Rwanda national health statistics unavailable.</div>`;
        }
    }


    //what the client can filter and sort for facilities

    function renderFacilities(){
        const keyword= filterInput.value.trim().toLowerCase();
        const sortBy= sortSelect.value;


        let filtered = currentFacilities.filter(item=>
            item.name.toLowerCase().includes(keyword) ||
            item.address.toLowerCase().includes(keyword)||
            item.district.toLowerCase().includes(keyword)
        );

        filtered.sort((a, b) => {
            if (sortBy=== "name-asc") return a.name.localeCompare(b.name);
            if (sortBy=== "name-desc") return b.name.localeCompare(a.name);
            return a.distance_km - b.distance_km;
        });

        statusBar.textContent= `Showing ${filtered.length} of ${currentFacilities.length} healthcare facilities near ${resolvedLocation}`;

        if(filtered.length===0){
            facilitiesGrid.innerHTML= `<p> No matching healthcare facilities found. Try a different keyword or town.</p>`;
            return
        }


        facilitiesGrid.innerHTML= filtered.map(item=>{
            const badgeClass= `badge-${item.type.toLowerCase()}`;
            const mapUrl= `https://google.com/maps/search/?api=1&query=${item.lat},${item.lon}`;

            return `
                <article class="facility-card">
                    <div>
                        <div class="card-top">
                            <h3 class="facility-name">${escapeHTML(item.name)}</h3>
                            <span class="badge ${badgeClass}">${escapeHTML(item.type)}</span>
                        </div>
                        <p class="facility-meta"><strong>Area:</strong> ${escapeHTML(item.district)}</p>
                        <p class="facility-meta">${escapeHTML(item.address)}</p>
                    </div>
                    <div class="card-footer">
                        <span><strong>${item.distance_km} km</strong> away</span>
                        <a href="${mapUrl}" target="_blank" rel="noopener" class="map-link">Open Map </a>
                    </div>
                
                </article>    
            `;
        }).join("");
    }

    //i writing a function that is going to retreive facilities from the flask backend
    async function fetchFacilities(){
        const city= cityInput.value.trim() || (presetCity.value !== "custom" ? presetCity.value: "");
        if (!city){
            showError("Please enter a town or district in Rwanda.");
            return;
        }

        hideError();
        statusBar.textContent= `Searching healthcare facilities near "${city}..."...`;
        facilitiesGrid.innerHTML= "";

        const params= new URLSearchParams({
            city: city,
            type: typeSelect.value
        });

        try{
            const res= await fetch(`/api/facilities?${params.toString()}`);
            const data= await res.json();


            if (!res.ok){
                throw new Error(data.error || "Failed to Fetch healthcare facilities.");
            }

            if (data.server && serverNameEl){
                serverNameEl.textContent= data.server;
            }


            currentFacilities= data.facilities || [];
            resolvedLocation= data.location || city;
            renderFacilities();
        } catch(err){
            showError(err.message);
        }
    }


    //i am gonna sync dropdown with the text input
    presetCity.addEventListener("change", ()=>{
        if (presetCity.value !== "custom"){
            cityInput.value= presetCity.value;
            fetchFacilities();
        }else{
            cityInput.value= "";
            cityInput.focus();
        }
    });

    cityInput.addEventListener("input", ()=>{
        const val= cityInput.value.trim().toLowerCase();
        const optionExists= Array.from(presetCity.options).some(opt => opt.value === val);
        presetCity.value=optionExists ? val: "custom";
    });

    cityInput.addEventListener("keypress", (e) => {
        if(e.key=== "Enter") fetchFacilities();
    });


    searchBtn.addEventListener("click", fetchFacilities);
    typeSelect.addEventListener("change", fetchFacilities);
    filterInput.addEventListener("input", renderFacilities);
    sortSelect.addEventListener("change", renderFacilities);


    //initial load
    loadHealthStats();
    fetchFacilities();
}); 