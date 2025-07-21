
import sqlite3
import chromadb
from pathlib import Path

from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

def populate_chroma_from_database():
    # Paths
    db_path = r"C:\Users\cyqt2\Database\overhaul\databases\meters.db"
    chroma_path = r"C:\Users\cyqt2\Database\overhaul\chroma_db\meters"
    
    # Check if database exists
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    # Create chroma directory if needed
    Path(chroma_path).mkdir(parents=True, exist_ok=True)
    

    # Load embedding model (Minilm from jina_reranker)

    embedding_model_path = r"C:/Users/cyqt2/Database/overhaul/jina_reranker/minilm-embedding"
    embedding_function = SentenceTransformerEmbeddingFunction(model_name=embedding_model_path)

    # Initialize Chroma with embedding function
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(
        "meters_semantic",
        embedding_function=embedding_function
    )
    
    # Check if already populated
    if collection.count() > 0:
        print(f"✅ Collection already has {collection.count()} documents")
        return True
    
    # Connect to SQLite
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get comprehensive meter data (matching your actual schema)
            query = """
            SELECT id, series_name, model_name, product_name, selection_blurb, 
                   device_short_name, product_type, display_type, display_resolution,
                   mounting_mode, mounting_support, rated_current, network_frequency,
                   sampling_rate, memory_capacity, width, height, depth, weight,
                   operating_altitude, operating_temp, storage_temp, relative_humidity,
                   pollution_degree, overvoltage_category
            FROM Meters
            ORDER BY series_name, model_name
            """
            
            cursor.execute(query)
            meters_data = cursor.fetchall()
            print(f"📊 Found {len(meters_data)} meters in database")
            
            if not meters_data:
                print("❌ No meters found in database")
                return False
            
            # Create documents for Chroma: per-meter and per-feature granularity
            documents = []
            metadatas = []
            ids = []
            doc_counter = 0
            for meter in meters_data:
                (meter_id, series_name, model_name, product_name, selection_blurb, 
                 device_short_name, product_type, display_type, display_resolution,
                 mounting_mode, mounting_support, rated_current, network_frequency,
                 sampling_rate, memory_capacity, width, height, depth, weight,
                 operating_altitude, operating_temp, storage_temp, relative_humidity,
                 pollution_degree, overvoltage_category) = meter

                # --- Per-meter document (as before) ---
                doc_parts = []
                if model_name:
                    doc_parts.append(f"Model: {model_name}")
                if series_name:
                    doc_parts.append(f"Series: {series_name}")
                if product_name:
                    doc_parts.append(f"Product: {product_name}")
                if product_type:
                    doc_parts.append(f"Type: {product_type}")
                if device_short_name:
                    doc_parts.append(f"Device: {device_short_name}")
                if selection_blurb:
                    doc_parts.append(f"Description: {selection_blurb}")
                if display_type:
                    doc_parts.append(f"Display: {display_type}")
                if display_resolution:
                    doc_parts.append(f"Resolution: {display_resolution}")
                if mounting_mode:
                    doc_parts.append(f"Mounting: {mounting_mode}")
                if rated_current:
                    doc_parts.append(f"Rated Current: {rated_current}")
                if network_frequency:
                    doc_parts.append(f"Frequency: {network_frequency}")
                if sampling_rate:
                    doc_parts.append(f"Sampling Rate: {sampling_rate}")
                if memory_capacity:
                    doc_parts.append(f"Memory: {memory_capacity}")
                if width and height and depth:
                    doc_parts.append(f"Dimensions: {width} x {height} x {depth}")
                if weight:
                    doc_parts.append(f"Weight: {weight}")
                if operating_temp:
                    doc_parts.append(f"Operating Temperature: {operating_temp}")
                if storage_temp:
                    doc_parts.append(f"Storage Temperature: {storage_temp}")
                if relative_humidity:
                    doc_parts.append(f"Humidity: {relative_humidity}")
                if operating_altitude:
                    doc_parts.append(f"Altitude: {operating_altitude}")
                if pollution_degree:
                    doc_parts.append(f"Pollution Degree: {pollution_degree}")
                if overvoltage_category:
                    doc_parts.append(f"Overvoltage Category: {overvoltage_category}")

                # Add per-meter doc
                meter_doc = "\n".join(doc_parts)
                documents.append(meter_doc)
                metadatas.append({
                    'meter_id': meter_id,
                    'model_name': model_name or 'Unknown',
                    'series_name': series_name or 'Unknown',
                    'product_type': product_type or 'Power Meter',
                    'doc_type': 'meter_summary'
                })
                ids.append(f"meter_{meter_id}")
                doc_counter += 1

                # --- Per-feature/measurement/accuracy/comm/etc. docs ---
                try:
                    # Accuracy
                    acc_query = "SELECT parameter, accuracy FROM MeasurementAccuracy WHERE meter_id = ?"
                    acc_data = cursor.execute(acc_query, (meter_id,)).fetchall()
                    for param, acc in acc_data:
                        if param and acc:
                            documents.append(f"{param}: {acc} (Model: {model_name}, Series: {series_name})")
                            metadatas.append({'meter_id': meter_id, 'feature_type': 'accuracy', 'parameter': param, 'model_name': model_name or 'Unknown'})
                            ids.append(f"meter_{meter_id}_accuracy_{param}")
                            doc_counter += 1

                    # Accuracy Class
                    acc_class_query = "SELECT accuracy_class FROM AccuracyClasses WHERE meter_id = ?"
                    acc_class_data = cursor.execute(acc_class_query, (meter_id,)).fetchall()
                    for ac in acc_class_data:
                        if ac[0]:
                            documents.append(f"Accuracy Class: {ac[0]} (Model: {model_name}, Series: {series_name})")
                            metadatas.append({'meter_id': meter_id, 'feature_type': 'accuracy_class', 'accuracy_class': ac[0], 'model_name': model_name or 'Unknown'})
                            ids.append(f"meter_{meter_id}_accclass_{ac[0]}")
                            doc_counter += 1

                    # Communication Protocols
                    comm_query = "SELECT protocol, support FROM CommunicationProtocols WHERE meter_id = ?"
                    comm_data = cursor.execute(comm_query, (meter_id,)).fetchall()
                    for p, s in comm_data:
                        if p:
                            proto_str = f"{p} ({s})" if s else p
                            documents.append(f"Communication: {proto_str} (Model: {model_name}, Series: {series_name})")
                            metadatas.append({'meter_id': meter_id, 'feature_type': 'communication', 'protocol': p, 'model_name': model_name or 'Unknown'})
                            ids.append(f"meter_{meter_id}_comm_{p}")
                            doc_counter += 1

                    # Power Quality Features
                    pq_query = "SELECT analysis_feature FROM PowerQualityAnalysis WHERE meter_id = ?"
                    pq_data = cursor.execute(pq_query, (meter_id,)).fetchall()
                    for f in pq_data:
                        if f[0]:
                            documents.append(f"Power Quality Feature: {f[0]} (Model: {model_name}, Series: {series_name})")
                            metadatas.append({'meter_id': meter_id, 'feature_type': 'power_quality', 'feature': f[0], 'model_name': model_name or 'Unknown'})
                            ids.append(f"meter_{meter_id}_pq_{f[0]}")
                            doc_counter += 1

                    # Measurements
                    meas_query = "SELECT measurement_type FROM Measurements WHERE meter_id = ?"
                    meas_data = cursor.execute(meas_query, (meter_id,)).fetchall()
                    for m in meas_data:
                        if m[0]:
                            documents.append(f"Measurement: {m[0]} (Model: {model_name}, Series: {series_name})")
                            metadatas.append({'meter_id': meter_id, 'feature_type': 'measurement', 'measurement': m[0], 'model_name': model_name or 'Unknown'})
                            ids.append(f"meter_{meter_id}_meas_{m[0]}")
                            doc_counter += 1

                    # Applications
                    app_query = "SELECT application FROM DeviceApplications WHERE meter_id = ?"
                    app_data = cursor.execute(app_query, (meter_id,)).fetchall()
                    for a in app_data:
                        if a[0]:
                            documents.append(f"Application: {a[0]} (Model: {model_name}, Series: {series_name})")
                            metadatas.append({'meter_id': meter_id, 'feature_type': 'application', 'application': a[0], 'model_name': model_name or 'Unknown'})
                            ids.append(f"meter_{meter_id}_app_{a[0]}")
                            doc_counter += 1

                    # Certifications
                    cert_query = "SELECT certification FROM Certifications WHERE meter_id = ?"
                    cert_data = cursor.execute(cert_query, (meter_id,)).fetchall()
                    for c in cert_data:
                        if c[0]:
                            documents.append(f"Certification: {c[0]} (Model: {model_name}, Series: {series_name})")
                            metadatas.append({'meter_id': meter_id, 'feature_type': 'certification', 'certification': c[0], 'model_name': model_name or 'Unknown'})
                            ids.append(f"meter_{meter_id}_cert_{c[0]}")
                            doc_counter += 1

                    # Data Recordings
                    rec_query = "SELECT recording_type FROM DataRecordings WHERE meter_id = ?"
                    rec_data = cursor.execute(rec_query, (meter_id,)).fetchall()
                    for r in rec_data:
                        if r[0]:
                            documents.append(f"Data Recording: {r[0]} (Model: {model_name}, Series: {series_name})")
                            metadatas.append({'meter_id': meter_id, 'feature_type': 'data_recording', 'recording_type': r[0], 'model_name': model_name or 'Unknown'})
                            ids.append(f"meter_{meter_id}_rec_{r[0]}")
                            doc_counter += 1

                    # Inputs/Outputs
                    io_query = "SELECT io_type, description FROM InputsOutputs WHERE meter_id = ?"
                    io_data = cursor.execute(io_query, (meter_id,)).fetchall()
                    for io in io_data:
                        if io[0]:
                            io_str = f"{io[0]} ({io[1]})" if io[1] else io[0]
                            documents.append(f"I/O: {io_str} (Model: {model_name}, Series: {series_name})")
                            metadatas.append({'meter_id': meter_id, 'feature_type': 'io', 'io_type': io[0], 'model_name': model_name or 'Unknown'})
                            ids.append(f"meter_{meter_id}_io_{io[0]}")
                            doc_counter += 1

                except Exception as e:
                    print(f"⚠️ Could not get additional data for meter {meter_id}: {e}")

            # Add all documents to Chroma
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✅ Added {doc_counter} documents (meter and features) to Chroma collection")

            # Verify with a test query
            test_results = collection.query(
                query_texts=["power meter with RS485 communication", "Real Power", "Frequency"],
                n_results=3
            )
            print(f"🔍 Test queries returned:")
            for idx, q in enumerate(["power meter with RS485 communication", "Real Power", "Frequency"]):
                docs = test_results['documents'][idx]
                print(f"  Query '{q}' -> {len(docs)} results")
                for i, doc in enumerate(docs):
                    print(f"    {i+1}. {doc[:150]}...")

            # Final verification
            final_count = collection.count()
            print(f"📊 Final collection count: {final_count}")
            return True
            
    except Exception as e:
        print(f"❌ Error populating Chroma: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    populate_chroma_from_database()