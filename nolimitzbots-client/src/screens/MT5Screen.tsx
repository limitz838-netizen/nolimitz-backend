import React, { useEffect, useState, useCallback, useRef } from "react";
import {
  ActivityIndicator,
  Alert,
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

type MT5ScreenProps = {
  licenseKey: string;
  onMT5StatusChange?: (connected: boolean) => void;
};

type MT5StatusResponse = {
  license_key: string;
  mt_login: string | null;
  mt_server: string | null;
  is_active: boolean;
  verified: boolean;
  account_name: string | null;
  broker_name: string | null;
  balance: string | null;
  equity: string | null;
  last_verified_at: string | null;
  status: string;
  message: string;
};

const API_BASE_URL = "https://dazedly-nondark-lise.ngrok-free.dev";

export default function MT5Screen({
  licenseKey,
  onMT5StatusChange,
}: MT5ScreenProps) {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [server, setServer] = useState("");

  const [loading, setLoading] = useState(false);
  const [statusLoading, setStatusLoading] = useState(true);
  const [mt5Status, setMT5Status] = useState<MT5StatusResponse | null>(null);

  const pollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearPollTimeout = () => {
    if (pollTimeoutRef.current) {
      clearTimeout(pollTimeoutRef.current);
      pollTimeoutRef.current = null;
    }
  };

  const parseJsonSafely = async (response: Response) => {
    const rawText = await response.text();

    console.log("MT5 RAW RESPONSE:", rawText);

    if (!rawText || !rawText.trim()) {
      return null;
    }

    try {
      return JSON.parse(rawText);
    } catch {
      throw new Error(rawText);
    }
  };

  const fetchMT5Status = useCallback(
    async (showLoading = true) => {
      if (!licenseKey.trim()) {
        setStatusLoading(false);
        return;
      }

      clearPollTimeout();

      try {
        if (showLoading) {
          setStatusLoading(true);
        }

        const response = await fetch(`${API_BASE_URL}/client/mt5/status`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ license_key: licenseKey }),
        });

        const data = (await parseJsonSafely(response)) as MT5StatusResponse | null;

        if (!response.ok) {
          const errorMsg =
            data?.message ||
            (data as any)?.detail ||
            "Failed to load MT5 status";
          throw new Error(errorMsg);
        }

        if (!data) {
          throw new Error("Empty response from MT5 status endpoint.");
        }

        setMT5Status(data);

        if (data.mt_login) {
          setLogin(data.mt_login);
        }

        if (data.mt_server) {
          setServer(data.mt_server);
        }

        const isConnectedNow = data.status === "connected";
        onMT5StatusChange?.(isConnectedNow);

        if (data.status === "verifying" || data.status === "retry") {
          pollTimeoutRef.current = setTimeout(() => {
            fetchMT5Status(false);
          }, 2500);
        }
      } catch (error) {
        console.error("MT5 status fetch error:", error);
        onMT5StatusChange?.(false);
      } finally {
        setStatusLoading(false);
      }
    },
    [licenseKey, onMT5StatusChange]
  );

  useEffect(() => {
    fetchMT5Status();

    return () => {
      clearPollTimeout();
    };
  }, [fetchMT5Status]);

  const handleSaveMT5 = async () => {
    if (!login.trim() || !password.trim() || !server.trim()) {
      Alert.alert("Missing Details", "Please enter login, password, and server.");
      return;
    }

    clearPollTimeout();

    try {
      setLoading(true);

      console.log("MT5 SAVE PAYLOAD", {
        login,
        passwordLength: password.length,
        server,
      });

      const response = await fetch(`${API_BASE_URL}/client/mt5/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          license_key: licenseKey,
          mt_login: login.trim(),
          mt_password: password.trim(),
          mt_server: server.trim(),
        }),
      });

      const data = await parseJsonSafely(response);

      if (!response.ok) {
        const errorMsg =
          data?.message ||
          data?.detail ||
          "Failed to save MT5 details";

        Alert.alert("Error", errorMsg);
        onMT5StatusChange?.(false);
        await fetchMT5Status(false);
        return;
      }

      Alert.alert(
        "Success",
        data?.message || "MT5 details saved. Verification started..."
      );

      setPassword("");
      onMT5StatusChange?.(false);

      await fetchMT5Status(false);
    } catch (error: any) {
      console.error("MT5 save error:", error);

      Alert.alert(
        "Connection Error",
        error?.message || "Could not connect to server. Please try again."
      );

      onMT5StatusChange?.(false);
    } finally {
      setLoading(false);
    }
  };

  const connectionStatus = mt5Status?.status ?? "not_connected";
  const isConnected = connectionStatus === "connected";
  const isVerifying =
    connectionStatus === "verifying" || connectionStatus === "retry";

  const statusLabel = isConnected
    ? "Connected"
    : isVerifying
      ? "Verifying..."
      : connectionStatus === "failed"
        ? "Verification Failed"
        : "Not Connected";

  const shownAccountName = isConnected ? mt5Status?.account_name || "—" : "—";
  const shownBrokerName = isConnected ? mt5Status?.broker_name || "—" : "—";
  const shownBalance =
    isConnected && mt5Status?.balance ? `$${mt5Status.balance}` : "—";

  const statusColor = isConnected
    ? "#56EBB9"
    : isVerifying
      ? "#7FDBFF"
      : connectionStatus === "failed"
        ? "#FF6B6B"
        : "#FFB4B4";

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
          <GlassCard style={styles.formCard}>
            <Text style={styles.title}>MT5 LOGIN DETAILS</Text>

            <View style={styles.fieldWrap}>
              <Text style={styles.label}>Login</Text>
              <TextInput
                value={login}
                onChangeText={setLogin}
                placeholder="Enter MT5 login"
                placeholderTextColor="rgba(255,255,255,0.38)"
                style={styles.input}
                keyboardType="number-pad"
                editable={!loading}
              />
            </View>

            <View style={styles.fieldWrap}>
              <Text style={styles.label}>Password</Text>
              <TextInput
                value={password}
                onChangeText={setPassword}
                placeholder="Enter MT5 password"
                placeholderTextColor="rgba(255,255,255,0.38)"
                style={styles.input}
                secureTextEntry
                editable={!loading}
              />
            </View>

            <View style={styles.fieldWrap}>
              <Text style={styles.label}>Server</Text>
              <TextInput
                value={server}
                onChangeText={setServer}
                placeholder="e.g. Exness-MT5Trial9"
                placeholderTextColor="rgba(255,255,255,0.38)"
                style={styles.input}
                editable={!loading}
              />
            </View>

            <Pressable
              style={[styles.saveButton, loading && styles.saveButtonDisabled]}
              onPress={handleSaveMT5}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#062B3D" />
              ) : (
                <>
                  <Ionicons name="save-outline" size={18} color="#062B3D" />
                  <Text style={styles.saveButtonText}>Save & Verify MT5</Text>
                </>
              )}
            </Pressable>
          </GlassCard>

          <GlassCard style={styles.statusCard}>
            <Text style={styles.statusTitle}>Connection Status</Text>

            {statusLoading ? (
              <View style={styles.statusLoadingWrap}>
                <ActivityIndicator color={Colors.primary} size="large" />
              </View>
            ) : (
              <>
                <View style={styles.statusRow}>
                  <Text style={styles.statusLabel}>Status</Text>
                  <Text style={[styles.statusValue, { color: statusColor }]}>
                    {statusLabel}
                  </Text>
                </View>

                <View
                  style={[
                    styles.messageBox,
                    connectionStatus === "failed" && styles.messageBoxFailed,
                  ]}
                >
                  <Text
                    style={[
                      styles.messageText,
                      connectionStatus === "failed" && styles.messageTextFailed,
                    ]}
                  >
                    {mt5Status?.message || "No MT5 status available."}
                  </Text>
                </View>

                {isConnected && (
                  <>
                    <View style={styles.statusRow}>
                      <Text style={styles.statusLabel}>Account Name</Text>
                      <Text style={styles.statusValue}>{shownAccountName}</Text>
                    </View>

                    <View style={styles.statusRow}>
                      <Text style={styles.statusLabel}>Broker</Text>
                      <Text style={styles.statusValue}>{shownBrokerName}</Text>
                    </View>

                    <View style={styles.statusRow}>
                      <Text style={styles.statusLabel}>Balance</Text>
                      <Text style={styles.statusValue}>{shownBalance}</Text>
                    </View>
                  </>
                )}
              </>
            )}
          </GlassCard>
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safe: { flex: 1 },
  content: {
    padding: Spacing.medium,
    paddingBottom: 36,
    gap: Spacing.medium,
  },

  formCard: {
    borderRadius: 28,
    padding: 22,
    backgroundColor: "rgba(255,255,255,0.06)",
    borderColor: "rgba(255,255,255,0.12)",
  },
  title: {
    color: "#F6FBFF",
    fontSize: 20,
    fontWeight: "900",
    textAlign: "center",
    marginBottom: 22,
    letterSpacing: 0.4,
  },

  fieldWrap: { marginBottom: 18 },
  label: {
    color: "rgba(240,248,255,0.92)",
    fontSize: 14,
    fontWeight: "700",
    marginBottom: 8,
  },
  input: {
    minHeight: 58,
    borderRadius: 18,
    paddingHorizontal: 18,
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "700",
    backgroundColor: "rgba(255,255,255,0.08)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.13)",
  },

  saveButton: {
    marginTop: 8,
    minHeight: 56,
    borderRadius: 18,
    backgroundColor: "#1ed1e1",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  saveButtonDisabled: { opacity: 0.7 },
  saveButtonText: {
    color: "#062B3D",
    fontSize: 16,
    fontWeight: "900",
  },

  statusCard: {
    borderRadius: 28,
    padding: 22,
    backgroundColor: "rgba(255,255,255,0.06)",
    borderColor: "rgba(255,255,255,0.12)",
  },
  statusTitle: {
    color: "#F6FBFF",
    fontSize: 18,
    fontWeight: "900",
    marginBottom: 18,
  },
  statusLoadingWrap: {
    minHeight: 120,
    alignItems: "center",
    justifyContent: "center",
  },
  statusRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 14,
  },
  statusLabel: {
    color: "rgba(214,234,255,0.78)",
    fontSize: 14,
    fontWeight: "600",
    flex: 1,
  },
  statusValue: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "800",
    flex: 1,
    textAlign: "right",
  },
  messageBox: {
    marginBottom: 14,
    padding: 12,
    borderRadius: 14,
    backgroundColor: "rgba(255,255,255,0.06)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.08)",
  },
  messageBoxFailed: {
    borderColor: "#FF6B6B",
  },
  messageText: {
    color: "rgba(230,240,255,0.88)",
    fontSize: 13,
    lineHeight: 18,
    fontWeight: "600",
  },
  messageTextFailed: {
    color: "#FF6B6B",
  },
});