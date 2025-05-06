import { useParams } from 'react-router-dom';
import Header from './Header';
import GeneratedNews from './GeneratedNews';
import ChatSection from './ChatSection';
import TimelineAnalysis from './TimelineAnalysis';
import './css/EventDetail.css';

function EventDetail() {
  const { eventId } = useParams();
  return (
    <div className='container'>
      <Header />
      <div className='content'>
        <GeneratedNews eventId={eventId} />
        <ChatSection eventId={eventId} />
      </div>     
      <TimelineAnalysis eventId={eventId} />
    </div>
  );
}

export default EventDetail;
