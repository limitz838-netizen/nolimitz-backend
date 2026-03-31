from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    admin_code = Column(String, unique=True, index=True, nullable=False)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("AdminProfile", back_populates="admin", uselist=False)
    eas = relationship("ExpertAdvisor", back_populates="admin")
    licenses = relationship("License", back_populates="admin")
    signals = relationship("Signal", back_populates="admin")


class AdminProfile(Base):
    __tablename__ = "admin_profiles"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), unique=True, nullable=False)
    display_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)

    admin = relationship("Admin", back_populates="profile")


class ExpertAdvisor(Base):
    __tablename__ = "expert_advisors"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    ea_code = Column(String, unique=True, index=True, nullable=False)
    mode = Column(String, default="signal")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin = relationship("Admin", back_populates="eas")
    licenses = relationship("License", back_populates="ea")
    signals = relationship("Signal", back_populates="ea")
    symbols = relationship("EASymbol", back_populates="ea", cascade="all, delete-orphan")


class EASymbol(Base):
    __tablename__ = "ea_symbols"

    id = Column(Integer, primary_key=True, index=True)
    ea_id = Column(Integer, ForeignKey("expert_advisors.id"), nullable=False)
    symbol = Column(String, nullable=False)

    ea = relationship("ExpertAdvisor", back_populates="symbols")


class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False)
    ea_id = Column(Integer, ForeignKey("expert_advisors.id"), nullable=False)
    client_name = Column(String, nullable=False)
    client_email = Column(String, nullable=False)
    license_key = Column(String, unique=True, index=True, nullable=False)
    device_id = Column(String, nullable=True)
    status = Column(String, default="active")
    duration_days = Column(Integer, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin = relationship("Admin", back_populates="licenses")
    ea = relationship("ExpertAdvisor", back_populates="licenses")
    client_account = relationship("ClientAccount", back_populates="license", uselist=False)


class ClientAccount(Base):
    __tablename__ = "client_accounts"

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), unique=True, nullable=False)

    mt_login = Column(String, nullable=False)
    mt_password = Column(String, nullable=False)
    mt_server = Column(String, nullable=False)

    broker_name = Column(String, nullable=True)
    is_connected = Column(Boolean, default=False)

    execute_trades = Column(Boolean, default=True)
    lot_size = Column(Float, default=0.01)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    license = relationship("License", back_populates="client_account")


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False)
    ea_id = Column(Integer, ForeignKey("expert_advisors.id"), nullable=False)
    symbol = Column(String, nullable=False)
    action = Column(String, nullable=False)   # buy or sell
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    status = Column(String, default="new")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin = relationship("Admin", back_populates="signals")
    ea = relationship("ExpertAdvisor", back_populates="signals")

class ClientSymbolSetting(Base):
    __tablename__ = "client_symbol_settings"

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False)
    symbol = Column(String, nullable=False)
    direction = Column(String, nullable=False, default="both")   # buy / sell / both
    lot_size = Column(String, nullable=False, default="0.01")
    platform = Column(String, nullable=False, default="mt5")     # mt4 / mt5
    max_trades = Column(String, nullable=False, default="1")
    is_enabled = Column(Boolean, default=True)

    license = relationship("License")

class TradeExecution(Base):
    __tablename__ = "trade_executions"

    id = Column(Integer, primary_key=True, index=True)

    license_id = Column(Integer, ForeignKey("licenses.id"))
    signal_id = Column(Integer, ForeignKey("signals.id"))

    symbol = Column(String)
    action = Column(String)

    success = Column(Boolean, default=False)
    message = Column(String)
    order_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ExecutionJob(Base):
    __tablename__ = "execution_jobs"

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False)

    symbol = Column(String, nullable=False)
    action = Column(String, nullable=False)
    volume = Column(Float, default=0.01)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)

    mt_login = Column(String)
    mt_password = Column(String)
    mt_server = Column(String)

    status = Column(String, default="pending")  # pending, processing, success, failed
    worker_name = Column(String, nullable=True)
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)