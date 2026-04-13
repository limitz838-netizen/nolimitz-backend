import React, { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";

import GlassCard from "../components/GlassCard";
import { Colors } from "../theme/colors";
import { Spacing } from "../theme/spacing";

type DirectionType = "buy" | "sell" | "both";

type PairConfig = {
  symbol: string;
  lotSize: string;
  direction: DirectionType;
  trades: string;
  maxOpenTrades: string;
  enabled: boolean;
};

type AllowedEASymbol = {
  id?: number;
  symbol_name: string;
};

type SymbolsListItem = {
  id: number;
  symbol_name: string;
  trade_direction: DirectionType;
  lot_size: string;
  max_open_trades: number;
  trades_per_signal: number;
  enabled: boolean;
};

type SymbolsScreenProps = {
  onBack?: () => void;
  licenseKey: string;
  onSymbolsStatusChange?: (configured: boolean) => void;
};

const API_BASE_URL = "https://dazedly-nondark-lise.ngrok-free.dev";

export default function SymbolsScreen({
  onBack,
  licenseKey,
  onSymbolsStatusChange,
}: SymbolsScreenProps) {
  const [availableSymbols, setAvailableSymbols] = useState<string[]>([]);
  const [configuredPairs, setConfiguredPairs] = useState<Record<string, PairConfig>>({});
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);

  const [lotSize, setLotSize] = useState("0.01");
  const [direction, setDirection] = useState<DirectionType>("both");
  const [trades, setTrades] = useState("1");
  const [maxOpenTrades, setMaxOpenTrades] = useState("1");

  const [loading, setLoading] = useState(false);
  const [listLoading, setListLoading] = useState(true);
  const [availableLoading, setAvailableLoading] = useState(true);

  const configuredList = useMemo(() => Object.values(configuredPairs), [configuredPairs]);

  const fetchAvailableSymbols = async () => {
  if (!licenseKey.trim()) {
    setAvailableSymbols([]);
    setAvailableLoading(false);
    return;
  }

  try {
    setAvailableLoading(true);

    const response = await fetch(`${API_BASE_URL}/client/symbols/allowed`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        license_key: licenseKey,
      }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data?.detail || "Failed to load allowed symbols");
    }

    let symbolsFromBackend: string[] = [];

    if (Array.isArray(data)) {
      symbolsFromBackend = data
        .map((item: any) =>
          typeof item === "string"
            ? item
            : item?.symbol_name || item?.symbol || item?.name
        )
        .filter(Boolean);
    } else if (Array.isArray(data?.symbols)) {
      symbolsFromBackend = data.symbols
        .map((item: any) =>
          typeof item === "string"
            ? item
            : item?.symbol_name || item?.symbol || item?.name
        )
        .filter(Boolean);
    } else if (Array.isArray(data?.allowed_symbols)) {
      symbolsFromBackend = data.allowed_symbols
        .map((item: any) =>
          typeof item === "string"
            ? item
            : item?.symbol_name || item?.symbol || item?.name
        )
        .filter(Boolean);
    }

    setAvailableSymbols([...new Set(symbolsFromBackend)]);
  } catch (error) {
    setAvailableSymbols([]);
    Alert.alert("Load Failed", "Could not load robot symbols from backend.");
  } finally {
    setAvailableLoading(false);
  }
};

  const fetchSavedSymbols = async () => {
    if (!licenseKey.trim()) {
      setListLoading(false);
      onSymbolsStatusChange?.(false);
      return;
    }

    try {
      setListLoading(true);

      const response = await fetch(`${API_BASE_URL}/client/symbols/list`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          license_key: licenseKey,
        }),
      });

      const data: SymbolsListItem[] = await response.json().catch(() => []);

      if (!response.ok) {
        throw new Error("Failed to load symbol settings");
      }

      const mapped: Record<string, PairConfig> = {};

      for (const item of data) {
        mapped[item.symbol_name] = {
          symbol: item.symbol_name,
          lotSize: item.lot_size,
          direction: item.trade_direction,
          trades: String(item.trades_per_signal || 1),
          maxOpenTrades: String(item.max_open_trades || 1),
          enabled: item.enabled,
        };
      }

      setConfiguredPairs(mapped);
      onSymbolsStatusChange?.(Object.keys(mapped).length > 0);
    } catch (error) {
      onSymbolsStatusChange?.(false);
    } finally {
      setListLoading(false);
    }
  };

  useEffect(() => {
    fetchAvailableSymbols();
    fetchSavedSymbols();
  }, [licenseKey]);

  const openConfigModal = (symbol: string) => {
    const existing = configuredPairs[symbol];

    setSelectedSymbol(symbol);
    setLotSize(existing?.lotSize ?? "0.01");
    setDirection(existing?.direction ?? "both");
    setTrades(existing?.trades ?? "1");
    setMaxOpenTrades(existing?.maxOpenTrades ?? "1");
  };

  const closeConfigModal = () => {
    setSelectedSymbol(null);
  };

  const savePairConfig = async () => {
    if (!selectedSymbol) return;

    if (!licenseKey.trim()) {
      Alert.alert("Missing License", "Please verify your license key first.");
      return;
    }

    try {
      setLoading(true);

      const response = await fetch(`${API_BASE_URL}/client/symbols/save`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          license_key: licenseKey,
          symbol_name: selectedSymbol,
          trade_direction: direction,
          lot_size: lotSize.trim() || "0.01",
          max_open_trades: Number(maxOpenTrades.trim() || "1"),
          trades_per_signal: Number(trades.trim() || "1"),
          enabled: true,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        Alert.alert(
          "Save Failed",
          data?.detail || "Could not save symbol settings."
        );
        return;
      }

      setConfiguredPairs((prev) => ({
        ...prev,
        [selectedSymbol]: {
          symbol: selectedSymbol,
          lotSize: lotSize.trim() || "0.01",
          direction,
          trades: trades.trim() || "1",
          maxOpenTrades: maxOpenTrades.trim() || "1",
          enabled: true,
        },
      }));

      onSymbolsStatusChange?.(true);
      Alert.alert("Success", "Symbol settings saved successfully.");
      closeConfigModal();
    } catch (error) {
      Alert.alert(
        "Connection Error",
        "Could not reach the server. Please check your internet or backend."
      );
    } finally {
      setLoading(false);
    }
  };

  const removeAllowedPair = (symbol: string) => {
    Alert.alert("Remove Symbol", `Remove ${symbol} from allowed symbols?`, [
      { text: "Cancel", style: "cancel" },
      {
        text: "Remove",
        style: "destructive",
        onPress: () => {
          setConfiguredPairs((prev) => {
            const copy = { ...prev };
            delete copy[symbol];
            const stillConfigured = Object.keys(copy).length > 0;
            onSymbolsStatusChange?.(stillConfigured);
            return copy;
          });
        },
      },
    ]);
  };

  return (
    <LinearGradient
      colors={["#050B18", "#09162E", "#0D2A57"]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={styles.container}
    >
      <SafeAreaView style={styles.safe}>
        <ScrollView
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.topRow}>
            <View style={styles.leftTop}>
              <Pressable style={styles.backButton} onPress={onBack}>
                <Ionicons name="arrow-back" size={18} color={Colors.text} />
              </Pressable>
              <Text style={styles.screenTitle}>NOLIMITZ PRO</Text>
            </View>
          </View>

          <GlassCard style={styles.noticeCard}>
            <Text style={styles.noticeText}>
              This are All the Symbols which this robot can trade. Select the one you
              want to allow.
            </Text>
          </GlassCard>

          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>All Symbols</Text>
            <Text style={styles.sectionHint}>Tap to configure</Text>
          </View>

          {availableLoading ? (
            <GlassCard style={styles.emptyCard}>
              <View style={styles.loadingWrap}>
                <ActivityIndicator color={Colors.primary} />
              </View>
            </GlassCard>
          ) : availableSymbols.length === 0 ? (
            <GlassCard style={styles.emptyCard}>
              <Text style={styles.emptyTitle}>No EA symbols found</Text>
            </GlassCard>
          ) : (
            availableSymbols.map((symbol) => (
              <Pressable key={symbol} onPress={() => openConfigModal(symbol)}>
                <GlassCard style={styles.pairCard}>
                  <Text style={styles.pairName}>{symbol}</Text>
                  <Ionicons
                    name="chevron-forward"
                    size={18}
                    color="rgba(255,255,255,0.75)"
                  />
                </GlassCard>
              </Pressable>
            ))
          )}

          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Allowed Symbols</Text>
            <Text style={styles.sectionHint}>{configuredList.length} selected</Text>
          </View>

          {listLoading ? (
            <GlassCard style={styles.emptyCard}>
              <View style={styles.loadingWrap}>
                <ActivityIndicator color={Colors.primary} />
              </View>
            </GlassCard>
          ) : configuredList.length === 0 ? (
            <GlassCard style={styles.emptyCard}>
              <Text style={styles.emptyTitle}>No symbols allowed yet</Text>
            </GlassCard>
          ) : (
            configuredList.map((item) => (
              <GlassCard key={item.symbol} style={styles.allowedCard}>
                <Text style={styles.allowedSymbol}>{item.symbol}</Text>

                <Pressable
                  onPress={() => removeAllowedPair(item.symbol)}
                  style={styles.removePill}
                >
                  <Ionicons name="trash-outline" size={14} color="#FF8EA3" />
                  <Text style={styles.removeText}>Remove</Text>
                </Pressable>
              </GlassCard>
            ))
          )}
        </ScrollView>

        <Modal
          visible={!!selectedSymbol}
          transparent
          animationType="fade"
          onRequestClose={closeConfigModal}
        >
          <View style={styles.modalOverlay}>
            <GlassCard style={styles.modalCard}>
              <View style={styles.modalHeader}>
                <View>
                  <Text style={styles.modalTitle}>{selectedSymbol}</Text>
                  <Text style={styles.modalSubTitle}>Configure this trading pair</Text>
                </View>

                <Pressable onPress={closeConfigModal} style={styles.modalClose}>
                  <Ionicons name="close" size={18} color={Colors.text} />
                </Pressable>
              </View>

              <ScrollView
                showsVerticalScrollIndicator={false}
                contentContainerStyle={styles.modalContent}
              >
                <View style={styles.inputWrap}>
                  <Text style={styles.label}>Lot Size</Text>
                  <TextInput
                    value={lotSize}
                    onChangeText={setLotSize}
                    placeholder="0.01"
                    placeholderTextColor="rgba(255,255,255,0.38)"
                    style={styles.input}
                    keyboardType="decimal-pad"
                    editable={!loading}
                  />
                </View>

                <View style={styles.inputWrap}>
                  <Text style={styles.label}>Direction</Text>
                  <View style={styles.optionRow}>
                    {(["buy", "sell", "both"] as DirectionType[]).map((item) => {
                      const active = direction === item;

                      return (
                        <Pressable
                          key={item}
                          onPress={() => setDirection(item)}
                          style={[
                            styles.optionButton,
                            active && styles.optionButtonActive,
                          ]}
                          disabled={loading}
                        >
                          <Text
                            style={[
                              styles.optionText,
                              active && styles.optionTextActive,
                            ]}
                          >
                            {item.toUpperCase()}
                          </Text>
                        </Pressable>
                      );
                    })}
                  </View>
                </View>

                <View style={styles.platformWrap}>
                  <Text style={styles.label}>Platform</Text>
                  <View style={styles.platformPill}>
                    <Text style={styles.platformPillText}>MT5</Text>
                  </View>
                </View>

                <View style={styles.inputWrap}>
                  <Text style={styles.label}>Number of Trades</Text>
                  <TextInput
                    value={trades}
                    onChangeText={setTrades}
                    placeholder="1"
                    placeholderTextColor="rgba(255,255,255,0.38)"
                    style={styles.input}
                    keyboardType="number-pad"
                    editable={!loading}
                  />
                </View>

                <View style={styles.inputWrap}>
                  <Text style={styles.label}>Max Open Trades</Text>
                  <TextInput
                    value={maxOpenTrades}
                    onChangeText={setMaxOpenTrades}
                    placeholder="1"
                    placeholderTextColor="rgba(255,255,255,0.38)"
                    style={styles.input}
                    keyboardType="number-pad"
                    editable={!loading}
                  />
                </View>

                <View style={styles.modalButtons}>
                  <Pressable
                    style={styles.cancelButton}
                    onPress={closeConfigModal}
                    disabled={loading}
                  >
                    <Text style={styles.cancelButtonText}>Cancel</Text>
                  </Pressable>

                  <Pressable
                    style={[styles.saveButton, loading && styles.saveButtonDisabled]}
                    onPress={savePairConfig}
                    disabled={loading}
                  >
                    {loading ? (
                      <ActivityIndicator color="#062B3D" />
                    ) : (
                      <Text style={styles.saveButtonText}>Save Pair</Text>
                    )}
                  </Pressable>
                </View>
              </ScrollView>
            </GlassCard>
          </View>
        </Modal>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safe: { flex: 1 },
  content: {
    padding: Spacing.medium,
    paddingBottom: 120,
  },

  topRow: {
    marginBottom: 18,
  },
  leftTop: {
    flexDirection: "row",
    alignItems: "center",
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.10)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.14)",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  screenTitle: {
    color: "#F6FBFF",
    fontSize: 21,
    fontWeight: "900",
    letterSpacing: 0.3,
  },

  noticeCard: {
    padding: 18,
    marginBottom: 18,
    borderRadius: 24,
    backgroundColor: "rgba(255,255,255,0.06)",
    borderColor: "rgba(255,255,255,0.12)",
  },
  noticeText: {
    color: "rgba(240,248,255,0.92)",
    fontSize: 14,
    lineHeight: 21,
    fontWeight: "600",
  },

  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
    marginTop: 2,
  },
  sectionTitle: {
    color: "#F6FBFF",
    fontSize: 18,
    fontWeight: "900",
  },
  sectionHint: {
    color: "rgba(214,234,255,0.82)",
    fontSize: 12,
    fontWeight: "700",
  },

  pairCard: {
    paddingVertical: 18,
    paddingHorizontal: 18,
    marginBottom: 12,
    borderRadius: 24,
    backgroundColor: "rgba(255,255,255,0.06)",
    borderColor: "rgba(255,255,255,0.12)",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  pairName: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "900",
    letterSpacing: 0.3,
  },

  emptyCard: {
    padding: 18,
    borderRadius: 22,
    backgroundColor: "rgba(255,255,255,0.06)",
    borderColor: "rgba(255,255,255,0.12)",
  },
  emptyTitle: {
    color: Colors.text,
    fontSize: 15,
    fontWeight: "800",
  },
  loadingWrap: {
    minHeight: 80,
    alignItems: "center",
    justifyContent: "center",
  },

  allowedCard: {
    paddingVertical: 18,
    paddingHorizontal: 18,
    marginBottom: 12,
    borderRadius: 24,
    backgroundColor: "rgba(255,255,255,0.06)",
    borderColor: "rgba(255,255,255,0.12)",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  allowedSymbol: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "900",
  },
  removePill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: "rgba(255,123,147,0.10)",
    borderWidth: 1,
    borderColor: "rgba(255,123,147,0.18)",
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 999,
  },
  removeText: {
    color: "#FF9DB0",
    fontSize: 12,
    fontWeight: "800",
  },

  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.62)",
    justifyContent: "center",
    padding: 22,
  },
  modalCard: {
    borderRadius: 24,
    padding: 16,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.14)",
    backgroundColor: "rgba(9,18,42,0.96)",
    maxHeight: "78%",
  },
  modalContent: {
    paddingBottom: 6,
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 14,
  },
  modalTitle: {
    color: "#FFFFFF",
    fontSize: 24,
    fontWeight: "900",
  },
  modalSubTitle: {
    color: "rgba(230,242,255,0.82)",
    fontSize: 13,
    marginTop: 3,
    fontWeight: "600",
  },
  modalClose: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: "rgba(255,255,255,0.10)",
    alignItems: "center",
    justifyContent: "center",
  },

  inputWrap: {
    marginBottom: 14,
  },
  label: {
    color: "#F0F7FF",
    fontSize: 13,
    marginBottom: 8,
    fontWeight: "700",
  },
  input: {
    backgroundColor: "rgba(255,255,255,0.08)",
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 14,
    color: "#FFFFFF",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.13)",
    fontSize: 15,
    fontWeight: "700",
  },

  optionRow: {
    flexDirection: "row",
    gap: 8,
  },
  optionButton: {
    flex: 1,
    minHeight: 50,
    backgroundColor: "rgba(255,255,255,0.08)",
    borderRadius: 16,
    paddingVertical: 12,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.13)",
  },
  optionButtonActive: {
    backgroundColor: "rgba(43,255,197,0.14)",
    borderColor: "rgba(43,255,197,0.34)",
  },
  optionText: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "900",
  },
  optionTextActive: {
    color: "#67FFC8",
  },

  platformWrap: {
    marginBottom: 14,
  },
  platformPill: {
    minHeight: 50,
    borderRadius: 16,
    backgroundColor: "rgba(43,255,197,0.14)",
    borderWidth: 1,
    borderColor: "rgba(43,255,197,0.34)",
    alignItems: "center",
    justifyContent: "center",
  },
  platformPillText: {
    color: "#67FFC8",
    fontSize: 14,
    fontWeight: "900",
  },

  modalButtons: {
    flexDirection: "row",
    gap: 10,
    marginTop: 8,
  },
  cancelButton: {
    flex: 1,
    height: 50,
    borderRadius: 16,
    backgroundColor: "rgba(255,255,255,0.08)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.13)",
    alignItems: "center",
    justifyContent: "center",
  },
  cancelButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "800",
  },
  saveButton: {
    flex: 1,
    height: 50,
    borderRadius: 16,
    backgroundColor: "#8BFFB8",
    alignItems: "center",
    justifyContent: "center",
  },
  saveButtonDisabled: {
    opacity: 0.7,
  },
  saveButtonText: {
    color: "#062B3D",
    fontSize: 14,
    fontWeight: "900",
  },
});