        # 🎭 ROL YÖNETİMİ TAB'I
        with tab_rol:
            st.subheader("🎭 Rol Yönetimi")
            st.caption("Sistemdeki rolleri buradan yönetebilirsiniz")
            
            # Yeni Rol Ekleme
            with st.expander("➕ Yeni Rol Ekle"):
                with st.form("new_role_form"):
                    new_rol_adi = st.text_input("Rol Adı", placeholder="örn: Laboratuvar Teknisyeni")
                    new_rol_aciklama = st.text_area("Açıklama", placeholder="Bu rolün görevleri...")
                    
                    if st.form_submit_button("Rolü Ekle"):
                        if new_rol_adi:
                            try:
                                with engine.connect() as conn:
                                    sql = "INSERT INTO ayarlar_roller (rol_adi, aciklama) VALUES (:r, :a)"
                                    conn.execute(text(sql), {"r": new_rol_adi, "a": new_rol_aciklama})
                                    conn.commit()
                                st.success(f"✅ '{new_rol_adi}' rolü eklendi!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Hata: {e}")
                        else:
                            st.warning("Rol adı zorunludur!")
            
            st.divider()
            
            # Mevcut Roller
            st.caption("📋 Mevcut Roller")
            try:
                roller_df = pd.read_sql("SELECT * FROM ayarlar_roller ORDER BY id", engine)
                
                if not roller_df.empty:
                    edited_roller = st.data_editor(
                        roller_df,
                        key="editor_roller",
                        column_config={
                            "id": st.column_config.NumberColumn("ID", disabled=True),
                            "rol_adi": st.column_config.TextColumn("Rol Adı", required=True),
                            "aciklama": st.column_config.TextColumn("Açıklama"),
                            "aktif": st.column_config.CheckboxColumn("Aktif"),
                            "olusturma_tarihi": None  # Gizle
                        },
                        use_container_width=True,
                        hide_index=True,
                        num_rows="dynamic"
                    )
                    
                    if st.button("💾 Rolleri Kaydet", use_container_width=True, type="primary"):
                        try:
                            edited_roller.to_sql("ayarlar_roller", engine, if_exists='replace', index=False)
                            st.success("✅ Roller güncellendi!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Kayıt hatası: {e}")
                else:
                    st.info("Henüz rol tanımlanmamış")
            except Exception as e:
                st.error(f"Roller yüklenirken hata: {e}")
        
        # 🏢 BÖLÜM YÖNETİMİ TAB'I
        with tab_bolum:
            st.subheader("🏢 Bölüm Yönetimi")
            st.caption("Fabrika bölümlerini buradan yönetebilirsiniz")
            
            # Yeni Bölüm Ekleme
            with st.expander("➕ Yeni Bölüm Ekle"):
                with st.form("new_bolum_form"):
                    new_bolum_adi = st.text_input("Bölüm Adı", placeholder="örn: Ar-Ge")
                    new_bolum_aciklama = st.text_area("Açıklama", placeholder="Bu bölümün görevleri...")
                    
                    if st.form_submit_button("Bölümü Ekle"):
                        if new_bolum_adi:
                            try:
                                with engine.connect() as conn:
                                    sql = "INSERT INTO ayarlar_bolumler (bolum_adi, aciklama) VALUES (:b, :a)"
                                    conn.execute(text(sql), {"b": new_bolum_adi, "a": new_bolum_aciklama})
                                    conn.commit()
                                st.success(f"✅ '{new_bolum_adi}' bölümü eklendi!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Hata: {e}")
                        else:
                            st.warning("Bölüm adı zorunludur!")
            
            st.divider()
            
            # Mevcut Bölümler
            st.caption("📋 Mevcut Bölümler")
            try:
                bolumler_df = pd.read_sql("SELECT * FROM ayarlar_bolumler ORDER BY id", engine)
                
                if not bolumler_df.empty:
                    edited_bolumler = st.data_editor(
                        bolumler_df,
                        key="editor_bolumler",
                        column_config={
                            "id": st.column_config.NumberColumn("ID", disabled=True),
                            "bolum_adi": st.column_config.TextColumn("Bölüm Adı", required=True),
                            "aciklama": st.column_config.TextColumn("Açıklama"),
                            "aktif": st.column_config.CheckboxColumn("Aktif"),
                            "olusturma_tarihi": None  # Gizle
                        },
                        use_container_width=True,
                        hide_index=True,
                        num_rows="dynamic"
                    )
                    
                    if st.button("💾 Bölümleri Kaydet", use_container_width=True, type="primary"):
                        try:
                            edited_bolumler.to_sql("ayarlar_bolumler", engine, if_exists='replace', index=False)
                            st.success("✅ Bölümler güncellendi!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Kayıt hatası: {e}")
                else:
                    st.info("Henüz bölüm tanımlanmamış")
            except Exception as e:
                st.error(f"Bölümler yüklenirken hata: {e}")
        
        # 🔑 YETKİ MATRİSİ TAB'I
        with tab_yetki:
            st.subheader("🔑 Yetki Matrisi")
            st.caption("Her rolün modül erişim yetkilerini buradan düzenleyebilirsiniz")
            
            try:
                # Rolleri çek
                roller_list = pd.read_sql("SELECT rol_adi FROM ayarlar_roller WHERE aktif=TRUE ORDER BY rol_adi", engine)
                
                if not roller_list.empty:
                    secili_rol = st.selectbox("Rol Seçin", roller_list['rol_adi'].tolist())
                    
                    # Modül listesi (sabit)
                    moduller = ["Üretim Girişi", "KPI Kontrol", "Personel Hijyen", "Temizlik Kontrol", "Raporlama", "Ayarlar"]
                    
                    # Bu rolün mevcut yetkilerini çek
                    mevcut_yetkiler = pd.read_sql(
                        f"SELECT modul_adi, erisim_turu FROM ayarlar_yetkiler WHERE rol_adi = '{secili_rol}'",
                        engine
                    )
                    
                    # Yetki matrisi oluştur
                    yetki_data = []
                    for modul in moduller:
                        mevcut = mevcut_yetkiler[mevcut_yetkiler['modul_adi'] == modul]
                        if not mevcut.empty:
                            erisim = mevcut.iloc[0]['erisim_turu']
                        else:
                            erisim = "Yok"
                        yetki_data.append({"Modül": modul, "Yetki": erisim})
                    
                    yetki_df = pd.DataFrame(yetki_data)
                    
                    # Düzenlenebilir tablo
                    edited_yetkiler = st.data_editor(
                        yetki_df,
                        key=f"editor_yetki_{secili_rol}",
                        column_config={
                            "Modül": st.column_config.TextColumn("Modül", disabled=True),
                            "Yetki": st.column_config.SelectboxColumn(
                                "Erişim Seviyesi",
                                options=["Yok", "Görüntüle", "Düzenle"],
                                required=True
                            )
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    if st.button(f"💾 {secili_rol} Yetkilerini Kaydet", use_container_width=True, type="primary"):
                        try:
                            with engine.connect() as conn:
                                # Önce bu rolün tüm yetkilerini sil
                                conn.execute(text(f"DELETE FROM ayarlar_yetkiler WHERE rol_adi = :r"), {"r": secili_rol})
                                
                                # Yeni yetkileri ekle
                                for _, row in edited_yetkiler.iterrows():
                                    sql = "INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES (:r, :m, :e)"
                                    conn.execute(text(sql), {"r": secili_rol, "m": row['Modül'], "e": row['Yetki']})
                                
                                conn.commit()
                            st.success(f"✅ {secili_rol} yetkileri güncellendi!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Kayıt hatası: {e}")
                else:
                    st.warning("Önce rol tanımlayın!")
            except Exception as e:
                st.error(f"Yetki matrisi yüklenirken hata: {e}")

