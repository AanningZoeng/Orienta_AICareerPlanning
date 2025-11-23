# AI职业规划系统 - 快速启动脚本

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AI Career Planning System - 启动向导" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "d:\python\Orienta_AICareerPlanning"

# 检查项目目录
if (-not (Test-Path $projectRoot)) {
    Write-Host "❌ 错误：项目目录不存在: $projectRoot" -ForegroundColor Red
    exit 1
}

Set-Location $projectRoot

Write-Host "📁 当前目录: $projectRoot" -ForegroundColor Green
Write-Host ""

# 检查Python
Write-Host "🔍 检查Python环境..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python已安装: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python未找到，请先安装Python" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 检查依赖
Write-Host "🔍 检查依赖包..." -ForegroundColor Yellow
$requirements = @("flask", "flask-cors", "python-dotenv")
$missingPackages = @()

foreach ($package in $requirements) {
    python -c "import $($package.Replace('-', '_'))" 2>$null
    if ($LASTEXITCODE -ne 0) {
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host "⚠️  缺少以下依赖包: $($missingPackages -join ', ')" -ForegroundColor Yellow
    Write-Host "📦 正在安装..." -ForegroundColor Yellow
    pip install $($missingPackages -join ' ')
} else {
    Write-Host "✅ 所有依赖已安装" -ForegroundColor Green
}

Write-Host ""

# 检查.env文件
Write-Host "🔍 检查配置文件..." -ForegroundColor Yellow
if (Test-Path "$projectRoot\.env") {
    Write-Host "✅ .env文件存在" -ForegroundColor Green
} else {
    Write-Host "⚠️  .env文件不存在，请先创建并配置API密钥" -ForegroundColor Yellow
}

Write-Host ""

# 显示菜单
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  请选择启动选项" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. 启动后端API服务器 (Flask)" -ForegroundColor White
Write-Host "  2. 打开前端测试页面" -ForegroundColor White
Write-Host "  3. 完整启动（后端 + 前端）" -ForegroundColor White
Write-Host "  4. 查看API文档" -ForegroundColor White
Write-Host "  5. 退出" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选项 (1-5)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🚀 启动Flask服务器..." -ForegroundColor Green
        Write-Host "   访问地址: http://localhost:5000" -ForegroundColor Cyan
        Write-Host "   前端页面: http://localhost:5000/index.html" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
        Write-Host ""
        python backend/api/server.py
    }
    
    "2" {
        Write-Host ""
        Write-Host "🌐 打开前端测试页面..." -ForegroundColor Green
        Start-Process "http://localhost:5000/test.html"
        Write-Host "✅ 浏览器已打开" -ForegroundColor Green
        Write-Host ""
        Write-Host "⚠️  注意：请确保后端服务器已启动！" -ForegroundColor Yellow
    }
    
    "3" {
        Write-Host ""
        Write-Host "🚀 启动完整系统..." -ForegroundColor Green
        Write-Host ""
        
        # 启动后端（后台运行）
        Write-Host "1️⃣  启动后端API服务器..." -ForegroundColor Cyan
        $backendJob = Start-Job -ScriptBlock {
            Set-Location "d:\python\Orienta_AICareerPlanning"
            python backend/api/server.py
        }
        
        Write-Host "   后端Job ID: $($backendJob.Id)" -ForegroundColor Gray
        Write-Host "   等待服务器启动..." -ForegroundColor Gray
        Start-Sleep -Seconds 3
        
        # 打开前端
        Write-Host ""
        Write-Host "2️⃣  打开前端测试页面..." -ForegroundColor Cyan
        Start-Process "http://localhost:5000/test.html"
        
        Write-Host ""
        Write-Host "✅ 系统启动完成！" -ForegroundColor Green
        Write-Host ""
        Write-Host "============================================" -ForegroundColor Cyan
        Write-Host "  访问地址:" -ForegroundColor White
        Write-Host "  📋 测试页面: http://localhost:5000/test.html" -ForegroundColor Cyan
        Write-Host "  🎨 主页面:   http://localhost:5000/index.html" -ForegroundColor Cyan
        Write-Host "  🔌 API文档:  http://localhost:5000/api/health" -ForegroundColor Cyan
        Write-Host "============================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "按任意键停止后端服务器..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        
        Write-Host ""
        Write-Host "🛑 停止后端服务器..." -ForegroundColor Red
        Stop-Job -Id $backendJob.Id
        Remove-Job -Id $backendJob.Id
        Write-Host "✅ 已停止" -ForegroundColor Green
    }
    
    "4" {
        Write-Host ""
        Write-Host "============================================" -ForegroundColor Cyan
        Write-Host "  API端点文档" -ForegroundColor Cyan
        Write-Host "============================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "基础URL: http://localhost:5000/api" -ForegroundColor White
        Write-Host ""
        Write-Host "📍 POST /api/major-research" -ForegroundColor Green
        Write-Host "   调用Major Research Agent" -ForegroundColor Gray
        Write-Host "   Body: { `"query`": `"用户兴趣描述`" }" -ForegroundColor Gray
        Write-Host ""
        Write-Host "📍 POST /api/career-analysis" -ForegroundColor Green
        Write-Host "   调用Career Analysis Agent" -ForegroundColor Gray
        Write-Host "   Body: { `"major_name`": `"专业名称`" }" -ForegroundColor Gray
        Write-Host ""
        Write-Host "📍 GET /api/health" -ForegroundColor Green
        Write-Host "   健康检查" -ForegroundColor Gray
        Write-Host ""
        Write-Host "详细文档: frontend/FRONTEND_README.md" -ForegroundColor Cyan
        Write-Host ""
    }
    
    "5" {
        Write-Host ""
        Write-Host "👋 再见！" -ForegroundColor Cyan
        exit 0
    }
    
    default {
        Write-Host ""
        Write-Host "❌ 无效选项" -ForegroundColor Red
    }
}

Write-Host ""
