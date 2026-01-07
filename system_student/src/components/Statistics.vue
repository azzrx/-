<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const statistics = ref({ 
  student_count: 0, 
  course_count: 0, 
  avg_score: 0, 
  attendance_rate: 0,
  course_statistics: []
})

const fetchStatistics = async () => {
  try {
    const response = await axios.get('/api/statistics')
    statistics.value = response.data
  } catch (error) {
    console.error('Error fetching statistics:', error)
  }
}

onMounted(() => {
  fetchStatistics()
})
</script>

<template>
  <div class="statistics-container">
    <h2 class="page-title">系统统计</h2>
    
    <!-- 总体统计卡片 -->
    <div class="overall-stats">
      <h3 class="section-title">总体统计</h3>
      <div class="stats-grid">
        <div class="stat-card student-count">
          <div class="stat-icon">👥</div>
          <div class="stat-content">
            <div class="stat-label">学生总数</div>
            <div class="stat-value">{{ statistics.student_count }}</div>
          </div>
        </div>
        
        <div class="stat-card course-count">
          <div class="stat-icon">📚</div>
          <div class="stat-content">
            <div class="stat-label">课程总数</div>
            <div class="stat-value">{{ statistics.course_count }}</div>
          </div>
        </div>
        
        <div class="stat-card avg-score">
          <div class="stat-icon">📊</div>
          <div class="stat-content">
            <div class="stat-label">平均成绩</div>
            <div class="stat-value">{{ statistics.avg_score }}</div>
          </div>
        </div>
        
        <div class="stat-card attendance-rate">
          <div class="stat-icon">✓</div>
          <div class="stat-content">
            <div class="stat-label">出勤率</div>
            <div class="stat-value">{{ statistics.attendance_rate }}%</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 分课程统计 -->
    <div class="course-stats-section">
      <h3 class="section-title">分课程统计</h3>
      <div v-if="statistics.course_statistics && statistics.course_statistics.length > 0" class="course-stats-wrapper">
        <table class="course-stats-table">
          <thead>
            <tr>
              <th>课程代码</th>
              <th>课程名称</th>
              <th>平均成绩</th>
              <th>出勤率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="course in statistics.course_statistics" :key="course.course_id">
              <td class="course-code">{{ course.course_code || '-' }}</td>
              <td class="course-name">{{ course.course_name }}</td>
              <td class="score">{{ course.avg_score }}</td>
              <td class="rate">
                <div class="rate-bar">
                  <div class="rate-fill" :style="{ width: course.attendance_rate + '%' }"></div>
                  <span class="rate-text">{{ course.attendance_rate }}%</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-state">
        <p>暂无课程统计数据</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.statistics-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  font-size: 28px;
  font-weight: bold;
  color: #2c3e50;
  margin: 0 0 30px 0;
  padding-bottom: 15px;
  border-bottom: 3px solid #3498db;
}

.overall-stats {
  margin-bottom: 40px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #34495e;
  margin: 0 0 20px 0;
  padding-left: 10px;
  border-left: 4px solid #3498db;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 25px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  color: white;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
}

.stat-card.student-count {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card.course-count {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card.avg-score {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-card.attendance-rate {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-icon {
  font-size: 48px;
  line-height: 1;
  opacity: 0.9;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 8px;
  font-weight: 500;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  line-height: 1;
}

.course-stats-section {
  margin-top: 30px;
}

.course-stats-wrapper {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.course-stats-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.course-stats-table thead {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.course-stats-table th {
  padding: 15px;
  text-align: left;
  font-weight: 600;
  font-size: 15px;
}

.course-stats-table tbody tr {
  border-bottom: 1px solid #e9ecef;
  transition: background-color 0.2s ease;
}

.course-stats-table tbody tr:hover {
  background-color: #f8f9fa;
}

.course-stats-table tbody tr:last-child {
  border-bottom: none;
}

.course-stats-table td {
  padding: 15px;
  color: #495057;
}

.course-code {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #6c757d;
}

.course-name {
  font-weight: 500;
  color: #212529;
}

.score {
  font-weight: 600;
  color: #007bff;
  font-size: 16px;
}

.rate {
  min-width: 120px;
}

.rate-bar {
  position: relative;
  width: 100%;
  height: 24px;
  background-color: #e9ecef;
  border-radius: 12px;
  overflow: hidden;
}

.rate-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%);
  border-radius: 12px;
  transition: width 0.3s ease;
}

.rate-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-weight: 600;
  font-size: 12px;
  color: #495057;
  z-index: 1;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 16px;
  background: #f8f9fa;
  border-radius: 10px;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-card {
    padding: 20px;
  }
  
  .stat-icon {
    font-size: 36px;
  }
  
  .stat-value {
    font-size: 24px;
  }
}
</style>

