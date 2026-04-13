import React, { useState } from "react";
import EntryScreen from "./src/screens/EntryScreen";
import LicenseKeyScreen from "./src/screens/LicenseKeyScreen";
import MainTabs from "./src/navigation/MainTabs";

type AppScreen = "entry" | "license" | "dashboard";
type ReturnTarget = "entry" | "dashboard";

type LicenseBranding = {
  licenseKey: string;
  robotName: string;
  activeUntil: string;
  ownerName: string;
  ownerContact: string;
  logoUrl: string;
  companyName: string;
};

export default function App() {
  const [screen, setScreen] = useState<AppScreen>("entry");
  const [licenseReturnTarget, setLicenseReturnTarget] =
    useState<ReturnTarget>("entry");

  const [branding, setBranding] = useState<LicenseBranding>({
    licenseKey: "",
    robotName: "",
    activeUntil: "",
    ownerName: "",
    ownerContact: "",
    logoUrl: "",
    companyName: "",
  });

  const openLicenseFromEntry = () => {
    setLicenseReturnTarget("entry");
    setScreen("license");
  };

  const openLicenseFromDashboard = () => {
    setLicenseReturnTarget("dashboard");
    setScreen("license");
  };

  const handleVerified = (data: LicenseBranding) => {
    setBranding(data);
    setScreen("dashboard");
  };

  const handleBackFromLicense = () => {
    setScreen(licenseReturnTarget === "dashboard" ? "dashboard" : "entry");
  };

  const handleDeleteRobot = () => {
    setBranding({
      licenseKey: "",
      robotName: "",
      activeUntil: "",
      ownerName: "",
      ownerContact: "",
      logoUrl: "",
      companyName: "",
    });
    setScreen("entry");
  };

  if (screen === "entry") {
    return <EntryScreen onAddEA={openLicenseFromEntry} />;
  }

  if (screen === "license") {
    return (
      <LicenseKeyScreen
        onBack={handleBackFromLicense}
        onVerified={handleVerified}
      />
    );
  }

  return (
    <MainTabs
      licenseKey={branding.licenseKey}
      robotName={branding.robotName}
      activeUntil={branding.activeUntil}
      ownerName={branding.ownerName}
      ownerContact={branding.ownerContact}
      logoUrl={branding.logoUrl}
      companyName={branding.companyName}
      onAddRobot={openLicenseFromDashboard}
      onDeleteRobot={handleDeleteRobot}
    />
  );
}