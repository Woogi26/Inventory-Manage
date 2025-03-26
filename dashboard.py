import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils import load_items, load_suppliers, load_inventory_transactions

def dashboard_app():
    st.title("재고관리 시스템 대시보드")
    
    # 데이터 로드
    items = load_items()
    suppliers = load_suppliers()
    transactions = load_inventory_transactions()
    
    # 주요 지표 계산
    total_items = len(items)
    total_suppliers = len(suppliers)
    
    # 현재 전체 재고 가치 계산
    total_stock_value = sum([
        item.get('stock', 0) * item.get('unit_price', 0) 
        for item in items
    ])
    
    # 최근 30일 거래 건수
    today = datetime.now().date()
    thirty_days_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    recent_transactions = [
        t for t in transactions 
        if t.get('transaction_date', '') >= thirty_days_ago
    ]
    
    recent_inbound = len([t for t in recent_transactions if t['transaction_type'] == '입고'])
    recent_outbound = len([t for t in recent_transactions if t['transaction_type'] == '출고'])
    
    # 대시보드 레이아웃
    st.markdown("### 주요 지표")
    
    # 주요 지표 카드 형태로 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="등록 물품 수", value=f"{total_items}개")
    
    with col2:
        st.metric(label="등록 거래처 수", value=f"{total_suppliers}개")
    
    with col3:
        st.metric(label="총 재고 가치", value=f"{total_stock_value:,.0f}원")
    
    with col4:
        st.metric(
            label="최근 30일 거래", 
            value=f"입고: {recent_inbound}건", 
            delta=f"출고: {recent_outbound}건"
        )
    
    # 재고 현황 섹션
    st.markdown("### 재고 현황")
    
    if items:
        # 재고 데이터 준비
        stock_data = []
        for item in items:
            stock_value = item.get('stock', 0) * item.get('unit_price', 0)
            
            # 거래처 정보 가져오기
            supplier_name = "없음"
            supplier_business_number = ""
            if item.get('supplier_id'):
                supplier = next((s for s in suppliers if s['id'] == item['supplier_id']), None)
                if supplier:
                    supplier_name = supplier['name']
                    supplier_business_number = supplier.get('business_number', '')
            
            stock_data.append({
                '물품명': item.get('name', ''),
                '품번': item.get('item_code', ''),
                '카테고리': item.get('category', '기타'),
                '재고': item.get('stock', 0),
                '단위': item.get('unit', ''),
                '단가': item.get('unit_price', 0),
                '재고가치': stock_value,
                '거래처': supplier_name,
                '사업자번호': supplier_business_number
            })
        
        stock_df = pd.DataFrame(stock_data)
        
        # 재고가 있는 항목만 필터링
        stock_with_value = stock_df[stock_df['재고'] > 0].sort_values(by='재고가치', ascending=False)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 상위 10개 물품의 재고 가치 차트
            if not stock_with_value.empty:
                top_items = stock_with_value.head(10)
                
                fig = px.bar(
                    top_items, 
                    x='물품명', 
                    y='재고가치',
                    title='상위 10개 물품 재고 가치',
                    labels={'재고가치': '재고 가치 (원)', '물품명': '물품명'},
                    color='카테고리',
                    hover_data=['품번']  # 품번 정보 툴팁에 추가
                )
                
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("재고가 있는 물품이 없습니다.")
        
        with col2:
            # 카테고리별 재고 비율 파이 차트
            if not stock_with_value.empty:
                category_data = stock_with_value.groupby('카테고리')['재고가치'].sum().reset_index()
                
                fig = px.pie(
                    category_data, 
                    names='카테고리', 
                    values='재고가치',
                    title='카테고리별 재고 가치 비율'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # 재고 상세 정보 표시
        st.markdown("#### 물품별 재고 상세")
        st.dataframe(stock_df.sort_values(by='재고가치', ascending=False))
    else:
        st.info("등록된 물품이 없습니다.")
    
    # 거래처 정보 섹션
    st.markdown("### 거래처 정보")
    
    if suppliers:
        suppliers_data = []
        for supplier in suppliers:
            suppliers_data.append({
                '거래처명': supplier.get('name', ''),
                '사업자번호': supplier.get('business_number', ''),
                '연락처': supplier.get('phone', ''),
                '이메일': supplier.get('email', ''),
                '주소': supplier.get('address', '')
            })
        
        suppliers_df = pd.DataFrame(suppliers_data)
        st.dataframe(suppliers_df)
    else:
        st.info("등록된 거래처가 없습니다.")
    
    # 최근 입출고 내역
    st.markdown("### 최근 입출고 내역")
    
    if transactions:
        # 최근 20개 거래만 표시
        recent_trans = transactions[-20:] if len(transactions) > 20 else transactions
        recent_trans.reverse()  # 최신 항목을 상단에 표시
        
        # 거래 데이터 변환
        trans_data = []
        for t in recent_trans:
            # 물품 정보
            item_name = "알 수 없음"
            item_code = ""
            item_unit = ""
            item = next((i for i in items if i['id'] == t['item_id']), None)
            if item:
                item_name = item['name']
                item_code = item.get('item_code', '')
                item_unit = item.get('unit', '')
            
            # 거래처 정보
            supplier_name = "없음"
            supplier_business_number = ""
            if t.get('supplier_id'):
                supplier = next((s for s in suppliers if s['id'] == t['supplier_id']), None)
                if supplier:
                    supplier_name = supplier['name']
                    supplier_business_number = supplier.get('business_number', '')
            
            trans_data.append({
                '날짜': t.get('transaction_date', ''),
                '유형': t['transaction_type'],
                '물품명': item_name,
                '품번': item_code,
                '수량': t['quantity'],
                '단위': item_unit,
                '거래처': supplier_name,
                '사업자번호': supplier_business_number,
                '비고': t.get('note', '')
            })
        
        trans_df = pd.DataFrame(trans_data)
        st.dataframe(trans_df)
        
        # 일별 입출고 추이 차트
        if len(transactions) > 0:
            # 거래 날짜 데이터 변환
            for t in transactions:
                if 'transaction_date' not in t:
                    t['transaction_date'] = datetime.now().strftime("%Y-%m-%d")
            
            # 날짜별 집계 데이터 만들기
            transactions_df = pd.DataFrame(transactions)
            transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])
            
            # 날짜별, 유형별 거래 건수 집계
            daily_trans = transactions_df.groupby([
                pd.Grouper(key='transaction_date', freq='D'), 'transaction_type'
            ]).size().reset_index(name='count')
            
            # 피벗 테이블로 변환
            pivot_df = daily_trans.pivot(
                index='transaction_date', 
                columns='transaction_type', 
                values='count'
            ).fillna(0).reset_index()
            
            # 누락된 컬럼 추가
            if '입고' not in pivot_df.columns:
                pivot_df['입고'] = 0
            if '출고' not in pivot_df.columns:
                pivot_df['출고'] = 0
            
            # 최근 30일 데이터만 필터링
            start_date = today - timedelta(days=30)
            pivot_df = pivot_df[pivot_df['transaction_date'] >= pd.Timestamp(start_date)]
            
            # 차트 그리기
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=pivot_df['transaction_date'],
                y=pivot_df['입고'],
                name='입고',
                line=dict(color='rgba(0, 128, 0, 0.8)', width=2),
                fill='tozeroy',
                mode='lines'
            ))
            
            fig.add_trace(go.Scatter(
                x=pivot_df['transaction_date'],
                y=pivot_df['출고'],
                name='출고',
                line=dict(color='rgba(255, 0, 0, 0.8)', width=2),
                fill='tozeroy',
                mode='lines'
            ))
            
            fig.update_layout(
                title='최근 30일 입출고 추이',
                xaxis_title='날짜',
                yaxis_title='거래 건수',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
    else:
        st.info("입출고 내역이 없습니다.") 