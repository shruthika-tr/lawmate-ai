import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { createClient } from "@supabase/supabase-js";

// Supabase client
const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

const LegalProfessionals = () => {
  const [searchParams] = useSearchParams();
  const [service, setService] = useState("");
  const [professionals, setProfessionals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const serviceParam = searchParams.get("service") || "";
    setService(serviceParam);

    const fetchProfessionals = async () => {
      setLoading(true);

      if (!serviceParam) {
        setProfessionals([]);
        setLoading(false);
        return;
      }

      // Query Supabase using the correct column `service_slug`
      const { data, error } = await supabase
        .from("legal_professionals")
        .select("*")
        .eq("service_slug", serviceParam)
        .eq("verified", true);

      if (error) {
        console.error("Error fetching legal professionals:", error);
        setProfessionals([]);
      } else {
        setProfessionals(data || []);
      }

      setLoading(false);
    };

    fetchProfessionals();
  }, [searchParams]);

  const handleSendRequest = (lawyer) => {
    alert(`Request sent to ${lawyer.name}`);
  };

  return (
    <main className="min-h-screen bg-black text-white">
      <div className="container max-w-6xl mx-auto px-6 py-24">
        <h1 className="text-3xl font-bold mb-8">
          Legal Professionals for{" "}
          {service ? decodeURIComponent(service) : "Selected Service"}
        </h1>

        {loading ? (
          <p className="text-gray-400">Loading professionals...</p>
        ) : professionals.length === 0 ? (
          <p className="text-gray-400">
            No verified professionals found for this service.
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {professionals.map((pro) => (
              <div
                key={pro.id}
                className="p-6 bg-white/5 rounded-xl border border-white/10 hover:shadow-lg transition-all"
              >
                <h2 className="text-xl font-semibold">{pro.name}</h2>
                <p className="text-gray-300 mt-1">
                  Specialization: {pro.specialization}
                </p>
                <p className="text-gray-300">
                  Experience: {pro.experience_years} years
                </p>
                <p className="text-gray-300">City: {pro.city}</p>
                <button
                  onClick={() => handleSendRequest(pro)}
                  className="mt-5 w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg transition"
                >
                  Send Request
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
};

export default LegalProfessionals;
